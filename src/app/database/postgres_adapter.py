"""PostgreSQL adapter for agent orchestration with high-concurrency support."""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import structlog

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, insert, update
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, Numeric, ForeignKey

from ..config import settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {'schema': 'documents'}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True)
    size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB)


class DocumentAnalysis(Base):
    __tablename__ = "document_analysis"
    __table_args__ = {'schema': 'analysis'}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.documents.id'))
    task_id = Column(String(255), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    extracted_metadata = Column(JSONB, nullable=False)
    confidence_score = Column(Numeric(3,2))
    requires_human_review = Column(Boolean, default=False)
    processing_start_time = Column(DateTime, nullable=False)
    processing_end_time = Column(DateTime, nullable=False)
    agents_used = Column(JSONB)
    successful_agents = Column(Integer, default=0)
    total_agents = Column(Integer, default=0)
    document_type = Column(String(50))
    contract_value = Column(Numeric(15,2))
    parties = Column(JSONB)
    key_dates = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentResult(Base):
    __tablename__ = "agent_results"
    __table_args__ = {'schema': 'agents'}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(PG_UUID(as_uuid=True), ForeignKey('analysis.document_analysis.id'))
    task_id = Column(String(255), nullable=False)
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)
    specialization = Column(String(50))
    status = Column(String(20), nullable=False)
    confidence = Column(Numeric(3,2))
    data = Column(JSONB)
    error_message = Column(Text)
    warnings = Column(JSONB)
    processing_time_ms = Column(Integer, nullable=False)
    agent_metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class PostgreSQLAdapter:
    """High-performance PostgreSQL adapter for agent orchestration."""
    
    def __init__(self):
        self.engine = create_async_engine(
            settings.async_database_url,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            echo=settings.debug  # SQL logging in debug mode
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self.logger = structlog.get_logger().bind(component="postgres_adapter")
        
    async def store_document_with_analysis(
        self,
        content: str,
        filename: str,
        analysis_result: Dict[str, Any],
        agent_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Store document, analysis, and agent results in a single transaction."""
        
        start_time = time.time()
        
        async with self.async_session() as session:
            try:
                async with session.begin():
                    # Calculate content hash for deduplication
                    import hashlib
                    content_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Check for existing document
                    existing_doc = await session.execute(
                        select(Document).where(Document.content_hash == content_hash)
                    )
                    existing_doc = existing_doc.scalar_one_or_none()
                    
                    if existing_doc:
                        document_id = existing_doc.id
                        self.logger.info(f"Using existing document: {document_id}")
                    else:
                        # Insert new document
                        document = Document(
                            filename=filename,
                            content=content,
                            content_hash=content_hash,
                            size_bytes=len(content.encode()),
                            mime_type=self._detect_mime_type(filename),
                            metadata={}
                        )
                        session.add(document)
                        await session.flush()  # Get the ID
                        document_id = document.id
                        
                        self.logger.info(f"Created new document: {document_id}")
                    
                    # Insert analysis result
                    analysis = DocumentAnalysis(
                        document_id=document_id,
                        task_id=analysis_result.get('task_id'),
                        analysis_type='orchestrated_agents',
                        extracted_metadata=analysis_result.get('extracted_metadata', {}),
                        confidence_score=analysis_result.get('confidence_score', 0.0),
                        requires_human_review=analysis_result.get('requires_human_review', False),
                        processing_start_time=datetime.fromtimestamp(analysis_result.get('processing_start_time', time.time())),
                        processing_end_time=datetime.fromtimestamp(analysis_result.get('processing_end_time', time.time())),
                        agents_used=analysis_result.get('agents_used', []),
                        successful_agents=analysis_result.get('successful_agents', 0),
                        total_agents=analysis_result.get('total_agents', 0),
                        document_type=self._extract_document_type(analysis_result),
                        contract_value=self._extract_contract_value(analysis_result),
                        parties=analysis_result.get('extracted_metadata', {}).get('parties', []),
                        key_dates=analysis_result.get('extracted_metadata', {}).get('key_dates', [])
                    )
                    session.add(analysis)
                    await session.flush()
                    analysis_id = analysis.id
                    
                    # Insert agent results
                    for agent_result in agent_results:
                        agent_record = AgentResult(
                            analysis_id=analysis_id,
                            task_id=agent_result.get('task_id'),
                            agent_name=agent_result.get('agent_name'),
                            agent_type=agent_result.get('agent_type', 'extraction'),
                            specialization=agent_result.get('specialization'),
                            status=agent_result.get('status'),
                            confidence=agent_result.get('confidence'),
                            data=agent_result.get('data', {}),
                            error_message=agent_result.get('error_message'),
                            warnings=agent_result.get('warnings', []),
                            processing_time_ms=agent_result.get('processing_time_ms', 0),
                            agent_metadata=agent_result.get('metadata', {})
                        )
                        session.add(agent_record)
                    
                    # Commit transaction
                    await session.commit()
                    
                    duration = time.time() - start_time
                    self.logger.info(
                        "Document and analysis stored successfully",
                        document_id=str(document_id),
                        analysis_id=str(analysis_id),
                        duration_ms=int(duration * 1000),
                        agent_count=len(agent_results)
                    )
                    
                    return {
                        'success': True,
                        'document_id': str(document_id),
                        'analysis_id': str(analysis_id),
                        'processing_time_ms': int(duration * 1000)
                    }
                    
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Storage transaction failed: {e}")
                raise
    
    async def search_documents(
        self,
        query: str,
        document_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents with filters."""
        
        async with self.async_session() as session:
            # Build dynamic query
            sql_query = text("""
                SELECT 
                    d.id as document_id,
                    d.filename,
                    d.upload_timestamp,
                    da.confidence_score,
                    da.document_type,
                    da.contract_value,
                    da.requires_human_review,
                    da.extracted_metadata,
                    SUBSTRING(d.content, 1, 500) as content_preview
                FROM documents.documents d
                JOIN analysis.document_analysis da ON d.id = da.document_id
                WHERE 
                    d.content ILIKE :query
                    AND da.confidence_score >= :min_confidence
                    AND (:document_type IS NULL OR da.document_type = :document_type)
                ORDER BY da.created_at DESC
                LIMIT :limit
            """)
            
            result = await session.execute(sql_query, {
                'query': f'%{query}%',
                'min_confidence': min_confidence,
                'document_type': document_type,
                'limit': limit
            })
            
            documents = []
            for row in result:
                documents.append({
                    'document_id': str(row.document_id),
                    'filename': row.filename,
                    'upload_timestamp': row.upload_timestamp.isoformat(),
                    'confidence_score': float(row.confidence_score) if row.confidence_score else 0.0,
                    'document_type': row.document_type,
                    'contract_value': float(row.contract_value) if row.contract_value else None,
                    'requires_human_review': row.requires_human_review,
                    'content_preview': row.content_preview,
                    'metadata_summary': row.extracted_metadata
                })
            
            return documents
    
    async def get_agent_performance_stats(
        self,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """Get agent performance statistics."""
        
        async with self.async_session() as session:
            # Agent success rates
            agent_stats_query = text("""
                SELECT 
                    agent_name,
                    COUNT(*) as total_executions,
                    AVG(confidence) as avg_confidence,
                    AVG(processing_time_ms) as avg_processing_time_ms,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
                    ROUND(
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 
                        2
                    ) as success_rate_percent
                FROM agents.agent_results
                WHERE created_at >= NOW() - INTERVAL ':hours_back hours'
                GROUP BY agent_name
                ORDER BY success_rate_percent DESC
            """)
            
            agent_result = await session.execute(agent_stats_query, {'hours_back': hours_back})
            
            agent_performance = []
            for row in agent_result:
                agent_performance.append({
                    'agent_name': row.agent_name,
                    'total_executions': row.total_executions,
                    'avg_confidence': float(row.avg_confidence) if row.avg_confidence else 0.0,
                    'avg_processing_time_ms': int(row.avg_processing_time_ms) if row.avg_processing_time_ms else 0,
                    'successful_executions': row.successful_executions,
                    'success_rate_percent': float(row.success_rate_percent)
                })
            
            # Overall system stats
            system_stats_query = text("""
                SELECT 
                    COUNT(DISTINCT da.id) as total_documents_processed,
                    AVG(da.confidence_score) as avg_confidence,
                    COUNT(CASE WHEN da.requires_human_review THEN 1 END) as documents_requiring_review,
                    COUNT(CASE WHEN da.contract_value > 1000000 THEN 1 END) as high_value_contracts
                FROM analysis.document_analysis da
                WHERE da.created_at >= NOW() - INTERVAL ':hours_back hours'
            """)
            
            system_result = await session.execute(system_stats_query, {'hours_back': hours_back})
            system_row = system_result.first()
            
            return {
                'time_period_hours': hours_back,
                'agent_performance': agent_performance,
                'system_stats': {
                    'total_documents_processed': system_row.total_documents_processed,
                    'avg_system_confidence': float(system_row.avg_confidence) if system_row.avg_confidence else 0.0,
                    'documents_requiring_review': system_row.documents_requiring_review,
                    'high_value_contracts': system_row.high_value_contracts
                }
            }
    
    async def get_review_queue(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get documents requiring human review."""
        
        async with self.async_session() as session:
            query = text("""
                SELECT 
                    da.id as analysis_id,
                    d.id as document_id,
                    d.filename,
                    da.confidence_score,
                    da.document_type,
                    da.contract_value,
                    da.extracted_metadata,
                    da.created_at
                FROM analysis.document_analysis da
                JOIN documents.documents d ON da.document_id = d.id
                WHERE da.requires_human_review = true
                ORDER BY 
                    CASE 
                        WHEN da.contract_value > 10000000 THEN 1  -- Critical priority
                        WHEN da.contract_value > 1000000 THEN 2   -- High priority  
                        WHEN da.confidence_score < 0.5 THEN 3     -- Low confidence
                        ELSE 4                                     -- Normal
                    END,
                    da.created_at DESC
                LIMIT :limit
            """)
            
            result = await session.execute(query, {'limit': limit})
            
            review_items = []
            for row in result:
                priority = 'critical' if row.contract_value and row.contract_value > 10000000 else \
                          'high' if row.contract_value and row.contract_value > 1000000 else \
                          'medium' if row.confidence_score and row.confidence_score < 0.5 else 'normal'
                
                review_items.append({
                    'analysis_id': str(row.analysis_id),
                    'document_id': str(row.document_id),
                    'filename': row.filename,
                    'confidence_score': float(row.confidence_score) if row.confidence_score else 0.0,
                    'document_type': row.document_type,
                    'contract_value': float(row.contract_value) if row.contract_value else None,
                    'priority': priority,
                    'created_at': row.created_at.isoformat(),
                    'extracted_metadata': row.extracted_metadata
                })
            
            return review_items
    
    def _detect_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def _extract_document_type(self, analysis_result: Dict[str, Any]) -> Optional[str]:
        """Extract document type from analysis result."""
        metadata = analysis_result.get('extracted_metadata', {})
        doc_type_info = metadata.get('document_type', {})
        
        if isinstance(doc_type_info, dict):
            return doc_type_info.get('primary')
        return str(doc_type_info) if doc_type_info else None
    
    def _extract_contract_value(self, analysis_result: Dict[str, Any]) -> Optional[float]:
        """Extract contract value from analysis result."""
        metadata = analysis_result.get('extracted_metadata', {})
        financial_terms = metadata.get('financial_terms', [])
        
        for term in financial_terms:
            if isinstance(term, dict) and term.get('type') == 'contract_value':
                return float(term.get('amount', 0))
        
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and connection status."""
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                
                # Check connection pool status
                pool = self.engine.pool
                
                return {
                    'status': 'healthy',
                    'database_url': settings.database_url.replace(settings.postgres_password, '***'),
                    'pool_status': {
                        'size': pool.size(),
                        'checked_in': pool.checkedin(),
                        'checked_out': pool.checkedout(),
                        'overflow': pool.overflow(),
                        'invalid': pool.invalid()
                    }
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()


# Global adapter instance
_db_adapter: Optional[PostgreSQLAdapter] = None

def get_db_adapter() -> PostgreSQLAdapter:
    """Get the global database adapter."""
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = PostgreSQLAdapter()
    return _db_adapter