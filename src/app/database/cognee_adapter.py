"""Adapter for Cognee database operations with concurrency handling."""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
import structlog
from .connection_manager import get_db_connection, DatabaseManager

logger = structlog.get_logger()


class CogneeAdapter:
    """Adapter for Cognee database operations with enhanced concurrency."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.logger = structlog.get_logger().bind(component="cognee_adapter")
    
    async def store_document_async(
        self, 
        content: str, 
        metadata: Dict[str, Any],
        database_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store document in Cognee with concurrency handling."""
        
        start_time = time.time()
        
        try:
            # Use load-balanced database selection if not specified
            result = await asyncio.to_thread(
                self._store_document_sync,
                content,
                metadata,
                database_name
            )
            
            duration = time.time() - start_time
            self.logger.info(
                "Document stored successfully",
                duration_ms=int(duration * 1000),
                database=database_name,
                size=len(content)
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Document storage failed",
                error=str(e),
                duration_ms=int(duration * 1000),
                database=database_name
            )
            raise
    
    def _store_document_sync(
        self,
        content: str,
        metadata: Dict[str, Any],
        database_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous document storage with retry logic."""
        
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                with get_db_connection(database_name) as conn:
                    # Prepare document data
                    document_data = {
                        'content': content,
                        'metadata': json.dumps(metadata),
                        'created_at': time.time(),
                        'size': len(content)
                    }
                    
                    # Store in documents table
                    cursor = conn.execute("""
                        INSERT INTO documents (content, metadata, created_at, size)
                        VALUES (?, ?, ?, ?)
                    """, (
                        document_data['content'],
                        document_data['metadata'],
                        document_data['created_at'],
                        document_data['size']
                    ))
                    
                    document_id = cursor.lastrowid
                    conn.commit()
                    
                    # Create embeddings (simplified)
                    embedding_result = self._create_embeddings_sync(
                        conn, document_id, content, metadata
                    )
                    
                    return {
                        'success': True,
                        'document_id': document_id,
                        'embedding_count': embedding_result.get('embedding_count', 0),
                        'database_used': database_name
                    }
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Storage attempt {attempt + 1} failed, retrying",
                        error=str(e),
                        retry_delay=retry_delay
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        raise Exception("All storage attempts failed")
    
    def _create_embeddings_sync(
        self,
        conn,
        document_id: int,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create embeddings for document content."""
        
        # Simplified embedding creation (would integrate with actual embedding service)
        chunks = self._chunk_content(content)
        embedding_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Placeholder for actual embedding generation
                embedding_vector = f"embedding_placeholder_{i}"  # Would be actual vector
                
                conn.execute("""
                    INSERT INTO embeddings (document_id, chunk_id, content, vector)
                    VALUES (?, ?, ?, ?)
                """, (document_id, i, chunk, embedding_vector))
                
                embedding_count += 1
                
            except Exception as e:
                self.logger.warning(f"Failed to create embedding for chunk {i}: {e}")
        
        conn.commit()
        return {'embedding_count': embedding_count}
    
    def _chunk_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """Split content into chunks for embedding."""
        chunks = []
        words = content.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def search_documents_async(
        self,
        query: str,
        limit: int = 10,
        database_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search documents with concurrency handling."""
        
        try:
            results = await asyncio.to_thread(
                self._search_documents_sync,
                query,
                limit,
                database_name
            )
            
            self.logger.info(
                "Document search completed",
                query_length=len(query),
                results_count=len(results),
                database=database_name
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Document search failed: {e}")
            raise
    
    def _search_documents_sync(
        self,
        query: str,
        limit: int = 10,
        database_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous document search."""
        
        with get_db_connection(database_name) as conn:
            # Simplified search (would use vector similarity in real implementation)
            cursor = conn.execute("""
                SELECT d.id, d.content, d.metadata, d.created_at
                FROM documents d
                WHERE d.content LIKE ?
                ORDER BY d.created_at DESC
                LIMIT ?
            """, (f'%{query}%', limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'content': row[1][:500] + '...' if len(row[1]) > 500 else row[1],
                    'metadata': json.loads(row[2]) if row[2] else {},
                    'created_at': row[3]
                })
            
            return results
    
    async def get_database_status(self) -> Dict[str, Any]:
        """Get status of all databases."""
        health_status = await self.db_manager.health_check()
        
        status = {
            'healthy_databases': sum(1 for is_healthy in health_status.values() if is_healthy),
            'total_databases': len(health_status),
            'database_health': health_status,
            'load_balancing_enabled': len(health_status) > 1
        }
        
        return status


# Factory function for easy initialization
def create_cognee_adapter(databases: Dict[str, str]) -> CogneeAdapter:
    """Create CogneeAdapter with database configuration."""
    from .connection_manager import initialize_database_manager, get_database_manager
    
    initialize_database_manager(databases)
    db_manager = get_database_manager()
    
    return CogneeAdapter(db_manager)