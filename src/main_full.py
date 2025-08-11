"""Main FastAPI application for agent orchestration service."""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from app.database.postgres_adapter import get_db_adapter
from app.services.orchestration import DocumentAnalysisOrchestrator
from app.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting agent orchestration service", version="1.0")
    
    # Initialize database connection
    db_adapter = get_db_adapter()
    health = await db_adapter.health_check()
    
    if health['status'] != 'healthy':
        logger.error("Database health check failed", health=health)
        raise RuntimeError("Database connection failed")
    
    logger.info("Database connection established", pool_status=health.get('pool_status'))
    
    # Initialize orchestrator
    app.state.orchestrator = DocumentAnalysisOrchestrator(db_adapter)
    app.state.db_adapter = db_adapter
    
    logger.info("Agent orchestration service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down agent orchestration service")
    await db_adapter.close()


app = FastAPI(
    title="Contract Agent Orchestration",
    description="High-performance agent orchestration for contract analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class DocumentAnalysisRequest(BaseModel):
    content: str
    filename: str
    priority: str = "normal"


class SearchRequest(BaseModel):
    query: str
    document_type: str = None
    min_confidence: float = 0.0
    limit: int = 10


class AnalysisResponse(BaseModel):
    success: bool
    task_id: str
    extracted_metadata: Dict[str, Any]
    confidence_score: float
    requires_human_review: bool
    processing_summary: Dict[str, Any]


# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_health = await app.state.db_adapter.health_check()
    
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
        "timestamp": time.time(),
        "service": "agent-orchestration",
        "database": db_health
    }


@app.post("/api/analyze-document", response_model=AnalysisResponse)
async def analyze_document(request: DocumentAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze document using agent orchestration."""
    
    logger.info(
        "Document analysis request received",
        filename=request.filename,
        content_length=len(request.content),
        priority=request.priority
    )
    
    try:
        # Run orchestrated analysis
        result = await app.state.orchestrator.analyze_document(
            document_content=request.content,
            filename=request.filename,
            priority=request.priority
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        # Store results in background
        background_tasks.add_task(
            store_analysis_results,
            request.content,
            request.filename,
            result
        )
        
        return AnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}", filename=request.filename)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search-documents")
async def search_documents(request: SearchRequest):
    """Search analyzed documents."""
    
    try:
        results = await app.state.db_adapter.search_documents(
            query=request.query,
            document_type=request.document_type,
            min_confidence=request.min_confidence,
            limit=request.limit
        )
        
        return {
            "success": True,
            "query": request.query,
            "results_count": len(results),
            "documents": results
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-performance")
async def get_agent_performance(hours_back: int = 24):
    """Get agent performance statistics."""
    
    try:
        stats = await app.state.db_adapter.get_agent_performance_stats(hours_back)
        return {
            "success": True,
            "performance_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Performance stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/review-queue")
async def get_review_queue(limit: int = 50):
    """Get documents requiring human review."""
    
    try:
        review_items = await app.state.db_adapter.get_review_queue(limit)
        
        return {
            "success": True,
            "review_count": len(review_items),
            "review_items": review_items
        }
        
    except Exception as e:
        logger.error(f"Review queue failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system-status")
async def get_system_status():
    """Get comprehensive system status."""
    
    try:
        # Get recent performance stats
        performance = await app.state.db_adapter.get_agent_performance_stats(1)  # Last hour
        
        # Get review queue size
        review_queue = await app.state.db_adapter.get_review_queue(1)
        
        # Database health
        db_health = await app.state.db_adapter.health_check()
        
        return {
            "success": True,
            "timestamp": time.time(),
            "system_health": {
                "database_status": db_health["status"],
                "connection_pool": db_health.get("pool_status", {}),
                "agents_active": len(performance.get("agent_performance", [])),
                "documents_processed_last_hour": performance.get("system_stats", {}).get("total_documents_processed", 0),
                "review_queue_size": len(review_queue)
            },
            "performance_summary": performance.get("system_stats", {}),
            "configuration": {
                "max_parallel_agents": settings.max_parallel_agents,
                "agent_timeout_seconds": settings.agent_timeout_seconds,
                "high_value_threshold": settings.high_value_threshold,
                "auto_approve_threshold": settings.auto_approve_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"System status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def store_analysis_results(
    content: str, 
    filename: str, 
    analysis_result: Dict[str, Any]
):
    """Store analysis results in database (background task)."""
    
    try:
        # Convert agent results to the format expected by database
        agent_results = []
        processing_metadata = analysis_result.get('extracted_metadata', {}).get('processing_metadata', {})
        
        # Create agent result records (simplified)
        agents_used = processing_metadata.get('agents_used', [])
        for agent_name in agents_used:
            agent_results.append({
                'task_id': analysis_result.get('task_id'),
                'agent_name': agent_name,
                'agent_type': 'extraction',
                'specialization': agent_name.lower().replace('agent', '').replace('classifier', 'classification'),
                'status': 'completed',  # Simplified - would track individual agent status
                'confidence': analysis_result.get('confidence_score', 0.5),
                'data': {},  # Would contain agent-specific data
                'processing_time_ms': processing_metadata.get('total_processing_time_ms', 0) // len(agents_used)
            })
        
        # Store in database
        storage_result = await app.state.db_adapter.store_document_with_analysis(
            content=content,
            filename=filename,
            analysis_result={
                **analysis_result,
                'processing_start_time': time.time() - (processing_metadata.get('total_processing_time_ms', 0) / 1000),
                'processing_end_time': time.time(),
                'agents_used': agents_used,
                'successful_agents': processing_metadata.get('successful_agents', len(agents_used)),
                'total_agents': processing_metadata.get('total_agents', len(agents_used))
            },
            agent_results=agent_results
        )
        
        logger.info(
            "Analysis results stored successfully",
            document_id=storage_result.get('document_id'),
            analysis_id=storage_result.get('analysis_id')
        )
        
    except Exception as e:
        logger.error(f"Failed to store analysis results: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )