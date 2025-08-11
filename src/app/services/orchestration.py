"""Main orchestration service that coordinates agents with database concurrency handling."""

import asyncio
import time
from typing import Dict, Any, List, Optional
from uuid import uuid4
import structlog

from crewai import Crew
from ..agents.extractors import (
    DocumentClassificationAgent, 
    PartyExtractionAgent, 
    FinancialAnalysisAgent
)
from ..agents.base import AgentResult, TaskStatus
from ..database.cognee_adapter import CogneeAdapter
from ..config import settings

logger = structlog.get_logger()


class DocumentAnalysisOrchestrator:
    """Orchestrates multiple agents for parallel document analysis with database concurrency handling."""
    
    def __init__(self, cognee_adapter: CogneeAdapter):
        self.cognee_adapter = cognee_adapter
        self.logger = structlog.get_logger().bind(component="orchestrator")
        
        # Initialize agents
        self.classification_agent = DocumentClassificationAgent()
        self.party_agent = PartyExtractionAgent()
        self.financial_agent = FinancialAnalysisAgent()
        
        self.agents = [
            self.classification_agent,
            self.party_agent,
            self.financial_agent
        ]
    
    async def analyze_document(
        self,
        document_content: str,
        filename: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Orchestrate parallel document analysis with database load balancing."""
        
        task_id = str(uuid4())
        start_time = time.time()
        
        self.logger.info(
            "Starting document analysis orchestration",
            task_id=task_id,
            filename=filename,
            content_length=len(document_content),
            priority=priority
        )
        
        try:
            # Stage 1: Parallel extraction
            extraction_results = await self._run_parallel_extraction(
                document_content, filename, task_id
            )
            
            # Stage 2: Validation and confidence assessment
            validation_result = await self._validate_extraction_results(
                extraction_results, document_content, task_id
            )
            
            # Stage 3: Database storage with load balancing
            storage_result = await self._store_results_with_load_balancing(
                document_content, validation_result, filename
            )
            
            # Stage 4: Final orchestration result
            final_result = await self._compile_final_result(
                extraction_results,
                validation_result,
                storage_result,
                task_id,
                start_time
            )
            
            self.logger.info(
                "Document analysis orchestration completed",
                task_id=task_id,
                total_duration_ms=int((time.time() - start_time) * 1000),
                confidence_score=final_result.get('confidence_score', 0),
                requires_review=final_result.get('requires_human_review', False)
            )
            
            return final_result
            
        except Exception as e:
            self.logger.error(
                "Document analysis orchestration failed",
                task_id=task_id,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    async def _run_parallel_extraction(
        self,
        content: str,
        filename: str,
        task_id: str
    ) -> Dict[str, AgentResult]:
        """Run extraction agents in parallel."""
        
        context = {
            'task_id': task_id,
            'filename': filename,
            'timestamp': time.time()
        }
        
        self.logger.info("Starting parallel extraction", task_id=task_id)
        
        # Create tasks for each agent
        tasks = [
            self.classification_agent.process(content, context),
            self.party_agent.process(content, context),
            self.financial_agent.process(content, context)
        ]
        
        # Run agents in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=settings.agent_timeout_seconds
            )
            
            # Process results
            extraction_results = {}
            for i, result in enumerate(results):
                agent_name = self.agents[i].agent_name
                
                if isinstance(result, Exception):
                    self.logger.error(f"Agent {agent_name} failed: {result}")
                    extraction_results[agent_name] = self._create_failed_result(
                        agent_name, task_id, str(result)
                    )
                else:
                    extraction_results[agent_name] = result
            
            return extraction_results
            
        except asyncio.TimeoutError:
            self.logger.error("Parallel extraction timed out", task_id=task_id)
            
            # Return partial results
            return {
                agent.agent_name: self._create_timeout_result(agent.agent_name, task_id)
                for agent in self.agents
            }
    
    async def _validate_extraction_results(
        self,
        extraction_results: Dict[str, AgentResult],
        content: str,
        task_id: str
    ) -> Dict[str, Any]:
        """Validate and cross-check extraction results."""
        
        self.logger.info("Starting result validation", task_id=task_id)
        
        # Count successful extractions
        successful_agents = sum(
            1 for result in extraction_results.values()
            if result.is_successful
        )
        
        # Calculate overall confidence
        confidence_scores = [
            result.confidence for result in extraction_results.values()
            if result.is_successful
        ]
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Apply business rules
        requires_review = self._apply_business_rules(extraction_results, content)
        
        # Determine final confidence
        if successful_agents == len(self.agents):
            final_confidence = overall_confidence * 1.1  # Boost for all agents successful
        elif successful_agents >= 2:
            final_confidence = overall_confidence * 0.9   # Slight reduction
        else:
            final_confidence = overall_confidence * 0.6   # Significant reduction
            requires_review = True
        
        final_confidence = min(final_confidence, 1.0)
        
        validation_result = {
            'overall_confidence': final_confidence,
            'successful_agents': successful_agents,
            'total_agents': len(self.agents),
            'requires_human_review': requires_review,
            'confidence_breakdown': {
                name: result.confidence for name, result in extraction_results.items()
                if result.is_successful
            },
            'validation_notes': self._generate_validation_notes(extraction_results, content)
        }
        
        return validation_result
    
    def _apply_business_rules(
        self,
        extraction_results: Dict[str, AgentResult],
        content: str
    ) -> bool:
        """Apply business rules to determine if human review is required."""
        
        requires_review = False
        
        # Check financial thresholds
        financial_result = extraction_results.get('FinancialAnalyzer')
        if financial_result and financial_result.is_successful:
            financial_terms = financial_result.data.get('financial_terms', [])
            
            for term in financial_terms:
                amount = term.get('amount', 0)
                if amount > settings.high_value_threshold:
                    requires_review = True
                    break
        
        # Check for critical keywords
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in settings.review_required_keywords):
            requires_review = True
        
        # Check extraction quality
        classification_result = extraction_results.get('DocumentClassifier')
        if classification_result and classification_result.confidence < 0.6:
            requires_review = True
        
        return requires_review
    
    def _generate_validation_notes(
        self,
        extraction_results: Dict[str, AgentResult],
        content: str
    ) -> List[str]:
        """Generate human-readable validation notes."""
        
        notes = []
        
        for agent_name, result in extraction_results.items():
            if not result.is_successful:
                notes.append(f"{agent_name} extraction failed: {result.error_message}")
            elif result.confidence < 0.6:
                notes.append(f"{agent_name} has low confidence: {result.confidence:.1%}")
        
        # Content analysis notes
        if len(content) < 200:
            notes.append("Document is very short, may lack sufficient information")
        
        if len(content) > 10000:
            notes.append("Document is very long, may require additional review")
        
        return notes
    
    async def _store_results_with_load_balancing(
        self,
        content: str,
        validation_result: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Store results using database load balancing."""
        
        # Determine which database to use based on document type/priority
        database_name = self._select_optimal_database(validation_result, filename)
        
        metadata = {
            'filename': filename,
            'validation_result': validation_result,
            'analysis_timestamp': time.time(),
            'orchestration_version': '1.0'
        }
        
        try:
            storage_result = await self.cognee_adapter.store_document_async(
                content=content,
                metadata=metadata,
                database_name=database_name
            )
            
            return storage_result
            
        except Exception as e:
            self.logger.error(f"Storage failed, trying fallback database: {e}")
            
            # Try with load balancing (no specific database)
            fallback_result = await self.cognee_adapter.store_document_async(
                content=content,
                metadata=metadata,
                database_name=None  # Let adapter choose
            )
            
            return fallback_result
    
    def _select_optimal_database(
        self,
        validation_result: Dict[str, Any],
        filename: str
    ) -> Optional[str]:
        """Select optimal database based on document characteristics."""
        
        # Business logic for database selection
        requires_review = validation_result.get('requires_human_review', False)
        confidence = validation_result.get('overall_confidence', 0.5)
        
        if requires_review or confidence < 0.6:
            return 'cognee-business'  # High-attention documents
        else:
            return 'cognee-dev'       # Standard processing
    
    async def _compile_final_result(
        self,
        extraction_results: Dict[str, AgentResult],
        validation_result: Dict[str, Any],
        storage_result: Dict[str, Any],
        task_id: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Compile final orchestration result."""
        
        # Merge extraction data
        merged_data = {}
        
        for agent_name, result in extraction_results.items():
            if result.is_successful:
                merged_data.update(result.data)
        
        # Add orchestration metadata
        merged_data['processing_metadata'] = {
            'task_id': task_id,
            'orchestration_type': 'parallel_agents',
            'total_processing_time_ms': int((time.time() - start_time) * 1000),
            'agents_used': list(extraction_results.keys()),
            'successful_agents': validation_result['successful_agents'],
            'confidence_score': validation_result['overall_confidence'],
            'requires_human_review': validation_result['requires_human_review'],
            'database_used': storage_result.get('database_used'),
            'document_id': storage_result.get('document_id'),
            'validation_notes': validation_result.get('validation_notes', [])
        }
        
        return {
            'success': True,
            'task_id': task_id,
            'extracted_metadata': merged_data,
            'confidence_score': validation_result['overall_confidence'],
            'requires_human_review': validation_result['requires_human_review'],
            'processing_summary': {
                'total_agents': len(extraction_results),
                'successful_agents': validation_result['successful_agents'],
                'storage_success': storage_result.get('success', False),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
        }
    
    def _create_failed_result(self, agent_name: str, task_id: str, error: str) -> AgentResult:
        """Create a failed result for an agent."""
        from ..agents.base import AgentResult, TaskStatus
        
        return AgentResult(
            agent_name=agent_name,
            task_id=task_id,
            status=TaskStatus.FAILED,
            confidence=0.0,
            data={},
            processing_time_ms=0,
            error_message=error
        )
    
    def _create_timeout_result(self, agent_name: str, task_id: str) -> AgentResult:
        """Create a timeout result for an agent."""
        from ..agents.base import AgentResult, TaskStatus
        
        return AgentResult(
            agent_name=agent_name,
            task_id=task_id,
            status=TaskStatus.TIMEOUT,
            confidence=0.0,
            data={},
            processing_time_ms=settings.agent_timeout_seconds * 1000,
            error_message="Agent execution timed out"
        )