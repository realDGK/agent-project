"""
Minimal FastAPI backend for contract analysis
Focus: Get functional database integration with basic AI analysis
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import asyncpg
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

genai.configure(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Contract Analysis Backend", version="1.0.0")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://agent_user:agent_password@localhost:5432/agent_orchestration"
)

class DocumentAnalysisRequest(BaseModel):
    content: str
    filename: str
    options: Dict[str, bool] = {}
    priority: str = "normal"

class DocumentAnalysisResult(BaseModel):
    document_id: str
    filename: str
    processing_time: float
    confidence_score: float
    extracted_metadata: Dict[str, Any]
    requires_human_review: bool
    processing_method: str
    analysis_timestamp: str

class DatabaseManager:
    def __init__(self):
        self.pool = None
        
    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    
    async def ensure_tables(self):
        """Ensure basic tables exist"""
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            # Basic documents table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    filename VARCHAR(255) NOT NULL,
                    content TEXT,
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Analysis results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS document_analysis (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                    extracted_metadata JSONB NOT NULL,
                    confidence_score DECIMAL(3,2) DEFAULT 0.0,
                    processing_method VARCHAR(100),
                    processing_time DECIMAL(6,2),
                    requires_human_review BOOLEAN DEFAULT FALSE,
                    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            logger.info("Database tables ensured")
    
    async def store_document(self, filename: str, content: str, file_size: int, mime_type: str) -> str:
        """Store document and return ID"""
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            document_id = await conn.fetchval("""
                INSERT INTO documents (filename, content, file_size, mime_type)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, filename, content, file_size, mime_type)
            
            return str(document_id)
    
    async def store_analysis(self, document_id: str, analysis_result: Dict[str, Any]) -> str:
        """Store analysis result and return analysis ID"""
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            analysis_id = await conn.fetchval("""
                INSERT INTO document_analysis (
                    document_id, extracted_metadata, confidence_score, 
                    processing_method, processing_time, requires_human_review
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, 
                uuid.UUID(document_id),
                json.dumps(analysis_result['extracted_metadata']),
                analysis_result['confidence_score'],
                analysis_result['processing_method'],
                analysis_result['processing_time'],
                analysis_result['requires_human_review']
            )
            
            return str(analysis_id)
    
    async def get_recent_documents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent documents with analysis"""
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    d.id as document_id,
                    d.filename,
                    d.created_at,
                    da.confidence_score,
                    da.requires_human_review,
                    da.processing_method
                FROM documents d
                LEFT JOIN document_analysis da ON d.id = da.document_id
                ORDER BY d.created_at DESC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]

# Global database manager
db = DatabaseManager()

class AIAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def extract_text_from_file(self, content: str, filename: str) -> str:
        """Extract text from various file formats"""
        try:
            if filename.lower().endswith('.pdf'):
                # For now, assume content is already text
                return content
            elif filename.lower().endswith(('.docx', '.doc')):
                # For now, assume content is already text  
                return content
            else:
                return content
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return content
    
    async def analyze_contract(self, content: str, filename: str, options: Dict[str, bool]) -> Dict[str, Any]:
        """Analyze contract using Google AI"""
        start_time = datetime.now()
        
        try:
            # Enhanced prompt for LegalBERT-style analysis
            use_legal_bert = options.get('useLegalBERT', False)
            track_lifecycle = options.get('trackLifecycle', False)
            extract_entities = options.get('extractEntities', False)
            
            # Build conditional JSON fields
            lifecycle_field = '"contract_relationships": {"parent_contract": "reference", "amendments": [], "related_documents": []},' if track_lifecycle else ""
            
            prompt = f"""
            Analyze this legal contract with high precision. Extract structured metadata in JSON format.
            
            Document: {filename}
            Content: {content[:5000]}...
            
            Analysis Requirements:
            {"- Use legal document expertise (LegalBERT-style analysis)" if use_legal_bert else ""}
            {"- Identify contract lifecycle elements (amendments, addendums, relationships)" if track_lifecycle else ""}
            {"- Extract all parties, entities, and their relationships" if extract_entities else ""}
            
            Return JSON with these exact fields:
            {{
                "document_type": {{
                    "primary": "contract_type",
                    "subcategory": "specific_type", 
                    "confidence": 0.95
                }},
                "parties": [
                    {{
                        "name": "Party Name",
                        "type": "client/vendor/contractor",
                        "legal_entity_type": "corporation/llc/individual"
                    }}
                ],
                "financial_terms": [
                    {{
                        "amount": 100000,
                        "currency": "USD",
                        "type": "total_value/payment/penalty"
                    }}
                ],
                "key_dates": {{
                    "execution_date": "YYYY-MM-DD",
                    "effective_date": "YYYY-MM-DD",
                    "expiration_date": "YYYY-MM-DD"
                }},
                "legal_terms": {{
                    "governing_law": "State/Country", 
                    "jurisdiction": "Location",
                    "dispute_resolution": "arbitration/litigation"
                }},
                {lifecycle_field}
                "risk_indicators": {{
                    "high_value": false,
                    "complex_terms": false,
                    "unusual_clauses": []
                }},
                "confidence_assessment": {{
                    "overall_confidence": 0.85,
                    "data_quality": "high/medium/low",
                    "extraction_notes": "Notes about extraction quality"
                }}
            }}
            
            Respond with ONLY the JSON, no additional text.
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            try:
                ai_metadata = json.loads(response.text.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response for {filename}")
                ai_metadata = self._fallback_extraction(content, filename)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determine confidence and review requirements
            confidence_score = ai_metadata.get('confidence_assessment', {}).get('overall_confidence', 0.7)
            financial_terms = ai_metadata.get('financial_terms', [])
            high_value = any(term.get('amount', 0) > 1000000 for term in financial_terms)
            
            requires_human_review = (
                confidence_score < 0.8 or 
                high_value or
                ai_metadata.get('risk_indicators', {}).get('complex_terms', False)
            )
            
            # Determine processing method
            processing_method = []
            if use_legal_bert:
                processing_method.append("LegalBERT")
            if track_lifecycle:
                processing_method.append("Lifecycle")
            if extract_entities:
                processing_method.append("Entities")
            processing_method.append("Gemini-AI")
            
            return {
                'extracted_metadata': ai_metadata,
                'confidence_score': confidence_score,
                'processing_time': processing_time,
                'requires_human_review': requires_human_review,
                'processing_method': " + ".join(processing_method) if processing_method else "Standard-AI"
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed for {filename}: {e}")
            return self._fallback_extraction(content, filename)
    
    def _fallback_extraction(self, content: str, filename: str) -> Dict[str, Any]:
        """Fallback extraction when AI fails"""
        return {
            'extracted_metadata': {
                'document_type': {'primary': 'Unknown', 'confidence': 0.3},
                'parties': [],
                'financial_terms': [],
                'key_dates': {},
                'legal_terms': {},
                'risk_indicators': {'high_value': False, 'complex_terms': False},
                'confidence_assessment': {
                    'overall_confidence': 0.3,
                    'data_quality': 'low',
                    'extraction_notes': 'Fallback extraction used - AI analysis failed'
                }
            },
            'confidence_score': 0.3,
            'processing_time': 1.0,
            'requires_human_review': True,
            'processing_method': 'Fallback-Extraction'
        }

# Global AI analyzer
ai_analyzer = AIAnalyzer()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await db.ensure_tables()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "contract-analysis-backend", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        async with db.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "connected",
                "ai_model": "ready"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.post("/api/analyze-document", response_model=DocumentAnalysisResult)
async def analyze_document(request: DocumentAnalysisRequest):
    """Analyze a single document"""
    try:
        logger.info(f"Analyzing document: {request.filename}")
        
        # Store document in database
        document_id = await db.store_document(
            filename=request.filename,
            content=request.content,
            file_size=len(request.content),
            mime_type="text/plain"  # Simplified for now
        )
        
        # Perform AI analysis
        analysis_result = await ai_analyzer.analyze_contract(
            content=request.content,
            filename=request.filename,
            options=request.options
        )
        
        # Store analysis results
        await db.store_analysis(document_id, analysis_result)
        
        # Return structured result
        return DocumentAnalysisResult(
            document_id=document_id,
            filename=request.filename,
            processing_time=analysis_result['processing_time'],
            confidence_score=analysis_result['confidence_score'],
            extracted_metadata=analysis_result['extracted_metadata'],
            requires_human_review=analysis_result['requires_human_review'],
            processing_method=analysis_result['processing_method'],
            analysis_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/documents")
async def get_recent_documents(limit: int = 20):
    """Get recent documents with analysis results"""
    try:
        documents = await db.get_recent_documents(limit)
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.get("/api/system-status")
async def system_status():
    """Get detailed system status"""
    try:
        recent_docs = await db.get_recent_documents(5)
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connection": "healthy",
                "recent_documents": len(recent_docs)
            },
            "ai_service": {
                "provider": "Google Gemini",
                "model": "gemini-1.5-flash",
                "status": "ready"
            },
            "features": {
                "document_upload": True,
                "ai_analysis": True,
                "legal_bert_simulation": True,
                "lifecycle_tracking": True,
                "entity_extraction": True,
                "database_storage": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"System status check failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)