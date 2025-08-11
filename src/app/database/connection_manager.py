"""Database connection manager with pooling and retry logic for high-concurrency access."""

import asyncio
import time
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, Generator, Dict, Any
from dataclasses import dataclass
from queue import Queue, Empty
import structlog

logger = structlog.get_logger()


@dataclass
class ConnectionConfig:
    """Database connection configuration."""
    database_url: str
    max_connections: int = 10
    connection_timeout: int = 30
    retry_attempts: int = 5
    retry_delay: float = 0.1
    busy_timeout: int = 30000  # SQLite busy timeout in ms


class SQLiteConnectionPool:
    """Thread-safe SQLite connection pool with retry logic."""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._pool: Queue = Queue(maxsize=config.max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Pre-create some connections
        self._initialize_pool()
        
        logger.info(
            "SQLite connection pool initialized",
            max_connections=config.max_connections,
            database=config.database_url
        )
    
    def _initialize_pool(self):
        """Create initial connections for the pool."""
        initial_connections = min(3, self.config.max_connections)  # Start with 3 connections
        
        for _ in range(initial_connections):
            try:
                conn = self._create_connection()
                self._pool.put(conn, block=False)
                self._created_connections += 1
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimized settings."""
        conn = sqlite3.Connection(
            self.config.database_url,
            timeout=self.config.connection_timeout,
            check_same_thread=False
        )
        
        # Configure SQLite for better concurrency
        conn.execute("PRAGMA busy_timeout = ?", (self.config.busy_timeout,))
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and performance
        conn.execute("PRAGMA cache_size = 10000")  # Increase cache size
        conn.execute("PRAGMA temp_store = MEMORY")  # Store temp data in memory
        
        return conn
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a connection from the pool with retry logic."""
        conn = None
        start_time = time.time()
        
        try:
            # Try to get connection from pool
            conn = self._acquire_connection()
            
            if conn is None:
                raise Exception("Failed to acquire database connection")
            
            # Test connection before use
            self._test_connection(conn)
            
            yield conn
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.warning("Database locked, implementing retry logic")
                conn = self._retry_connection()
                yield conn
            else:
                raise
                
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
            
        finally:
            if conn:
                self._release_connection(conn)
                
            duration = time.time() - start_time
            if duration > 1.0:  # Log slow connections
                logger.warning(f"Slow database connection: {duration:.2f}s")
    
    def _acquire_connection(self) -> Optional[sqlite3.Connection]:
        """Acquire a connection from the pool."""
        try:
            # Try to get existing connection
            return self._pool.get(block=False)
        except Empty:
            # Pool is empty, try to create new connection
            with self._lock:
                if self._created_connections < self.config.max_connections:
                    try:
                        conn = self._create_connection()
                        self._created_connections += 1
                        return conn
                    except Exception as e:
                        logger.error(f"Failed to create new connection: {e}")
                        return None
                else:
                    # Pool is full, wait for available connection
                    try:
                        return self._pool.get(timeout=self.config.connection_timeout)
                    except Empty:
                        logger.error("Connection pool timeout")
                        return None
    
    def _retry_connection(self) -> sqlite3.Connection:
        """Retry connection with exponential backoff."""
        for attempt in range(self.config.retry_attempts):
            try:
                delay = self.config.retry_delay * (2 ** attempt)
                time.sleep(delay)
                
                logger.info(f"Retry attempt {attempt + 1}/{self.config.retry_attempts}")
                
                # Try to create a fresh connection
                conn = self._create_connection()
                self._test_connection(conn)
                
                return conn
                
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                
                if attempt == self.config.retry_attempts - 1:
                    logger.error("All retry attempts exhausted")
                    raise
        
        raise Exception("Failed to establish database connection after retries")
    
    def _test_connection(self, conn: sqlite3.Connection):
        """Test if connection is working."""
        try:
            conn.execute("SELECT 1").fetchone()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    def _release_connection(self, conn: sqlite3.Connection):
        """Return connection to pool."""
        try:
            # Rollback any pending transactions
            conn.rollback()
            
            # Put connection back in pool
            self._pool.put(conn, block=False)
            
        except Exception as e:
            # Connection is bad, don't return to pool
            logger.warning(f"Failed to return connection to pool: {e}")
            with self._lock:
                self._created_connections -= 1


class DatabaseManager:
    """High-level database manager with load balancing."""
    
    def __init__(self, databases: Dict[str, str]):
        """Initialize with multiple database URLs for load balancing."""
        self.pools = {}
        self.database_names = list(databases.keys())
        self._round_robin_index = 0
        
        # Create connection pool for each database
        for name, url in databases.items():
            config = ConnectionConfig(
                database_url=url,
                max_connections=8,  # Reduced per database
                connection_timeout=10,
                retry_attempts=3
            )
            self.pools[name] = SQLiteConnectionPool(config)
            
        logger.info(f"DatabaseManager initialized with {len(self.pools)} databases")
    
    @contextmanager
    def get_connection(self, database_name: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
        """Get connection with optional load balancing."""
        if database_name is None:
            # Round-robin load balancing
            database_name = self._get_next_database()
        
        if database_name not in self.pools:
            raise ValueError(f"Database '{database_name}' not configured")
        
        with self.pools[database_name].get_connection() as conn:
            yield conn
    
    def _get_next_database(self) -> str:
        """Get next database for round-robin load balancing."""
        database_name = self.database_names[self._round_robin_index]
        self._round_robin_index = (self._round_robin_index + 1) % len(self.database_names)
        return database_name
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        health_status = {}
        
        for name, pool in self.pools.items():
            try:
                with pool.get_connection() as conn:
                    conn.execute("SELECT 1").fetchone()
                    health_status[name] = True
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = False
        
        return health_status


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def initialize_database_manager(databases: Dict[str, str]):
    """Initialize the global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(databases)


def get_database_manager() -> DatabaseManager:
    """Get the global database manager."""
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database_manager() first.")
    return _db_manager


# Context manager for easy access
@contextmanager
def get_db_connection(database_name: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Convenience function to get database connection."""
    manager = get_database_manager()
    with manager.get_connection(database_name) as conn:
        yield conn