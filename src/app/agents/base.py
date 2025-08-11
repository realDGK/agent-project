"""Base agent classes and common functionality."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class ConfidenceLevel(Enum):
    """Confidence levels for agent outputs."""
    HIGH = "high"      # 85%+
    MEDIUM = "medium"  # 60-84%
    LOW = "low"        # <60%


class TaskStatus(Enum):
    """Status of agent tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResult:
    """Standard result structure for all agents."""
    agent_name: str
    task_id: str
    status: TaskStatus
    confidence: float
    data: Dict[str, Any]
    processing_time_ms: int
    error_message: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum based on score."""
        if self.confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.60:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    @property
    def is_successful(self) -> bool:
        """Check if the agent task was successful."""
        return self.status == TaskStatus.COMPLETED and self.error_message is None


class BaseAgent(ABC):
    """Base class for all contract analysis agents."""
    
    def __init__(self, agent_name: str, description: str = ""):
        self.agent_name = agent_name
        self.description = description
        self.logger = structlog.get_logger().bind(agent=agent_name)
    
    @abstractmethod
    async def process(self, document_content: str, context: Dict[str, Any]) -> AgentResult:
        """Process document content and return structured results."""
        pass
    
    def _create_result(
        self, 
        task_id: str,
        status: TaskStatus, 
        confidence: float, 
        data: Dict[str, Any],
        processing_time_ms: int,
        error_message: Optional[str] = None,
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> AgentResult:
        """Helper to create standardized results."""
        return AgentResult(
            agent_name=self.agent_name,
            task_id=task_id,
            status=status,
            confidence=confidence,
            data=data,
            processing_time_ms=processing_time_ms,
            error_message=error_message,
            warnings=warnings or [],
            metadata=metadata or {}
        )


class ExtractionAgent(BaseAgent):
    """Base class for data extraction agents."""
    
    def __init__(self, agent_name: str, description: str = ""):
        super().__init__(agent_name, description)
        self.extraction_patterns = {}
    
    @abstractmethod
    async def extract_data(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific data from document content."""
        pass


class ValidationAgent(BaseAgent):
    """Base class for validation agents."""
    
    def __init__(self, agent_name: str, description: str = ""):
        super().__init__(agent_name, description)
        self.validation_rules = []
    
    @abstractmethod
    async def validate_data(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted data and return validation results."""
        pass


class SupervisorAgent(BaseAgent):
    """Base class for supervisor agents that coordinate other agents."""
    
    def __init__(self, agent_name: str, description: str = ""):
        super().__init__(agent_name, description)
        self.managed_agents = []
    
    @abstractmethod
    async def coordinate(self, agent_results: List[AgentResult], context: Dict[str, Any]) -> AgentResult:
        """Coordinate multiple agent results into final decision."""
        pass