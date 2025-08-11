"""Configuration settings for the agent orchestration system."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    app_name: str = "Contract Agent Orchestration"
    debug: bool = False
    log_level: str = "INFO"
    
    # LLM Configuration
    google_api_key: str
    openai_api_key: Optional[str] = None
    llm_model: str = "gemini-2.0-flash-exp"
    embedding_model: str = "gemini-embedding-001"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "cognee_user"
    postgres_password: str
    postgres_db: str = "cognee_agents"
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 30
    
    # PgBouncer Configuration (for connection pooling)
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 6432
    use_pgbouncer: bool = True
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL."""
        if self.use_pgbouncer:
            host, port = self.pgbouncer_host, self.pgbouncer_port
        else:
            host, port = self.postgres_host, self.postgres_port
            
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{host}:{port}/{self.postgres_db}"
    
    @property 
    def async_database_url(self) -> str:
        """Get async PostgreSQL connection URL."""
        if self.use_pgbouncer:
            host, port = self.pgbouncer_host, self.pgbouncer_port
        else:
            host, port = self.postgres_host, self.postgres_port
            
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{host}:{port}/{self.postgres_db}"
    
    # Agent Configuration
    max_parallel_agents: int = 6
    agent_timeout_seconds: int = 120
    validation_timeout_seconds: int = 60
    
    # Business Rules
    high_value_threshold: int = 10000000  # $10M
    review_required_keywords: list = [
        "termination", "breach", "penalty", "liquidated damages", 
        "indemnification", "liability", "force majeure"
    ]
    
    # Confidence Thresholds
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.60
    auto_approve_threshold: float = 0.80
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()