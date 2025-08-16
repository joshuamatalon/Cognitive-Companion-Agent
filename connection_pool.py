"""
Connection pooling for efficient API client management.
"""
from typing import Dict, Any, Optional, Callable
import threading
from queue import Queue, Empty, Full
import time
from contextlib import contextmanager
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Information about a pooled connection."""
    connection: Any
    created_at: float
    last_used: float
    use_count: int = 0

class ConnectionPool:
    """Thread-safe connection pool for API clients."""
    
    def __init__(
        self, 
        factory: Callable,
        max_size: int = 10,
        min_size: int = 1,
        max_idle_time: int = 300,
        max_lifetime: int = 3600,
        name: str = "pool"
    ):
        """
        Initialize connection pool.
        
        Args:
            factory: Callable that creates new connections
            max_size: Maximum pool size
            min_size: Minimum number of connections to maintain
            max_idle_time: Max seconds a connection can be idle
            max_lifetime: Max seconds a connection can live
            name: Pool name for logging
        """
        self.factory = factory
        self.max_size = max_size
        self.min_size = min_size
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime
        self.name = name
        
        self.pool = Queue(maxsize=max_size)
        self.active_connections = 0
        self.total_connections_created = 0
        self.lock = threading.Lock()
        
        self.stats = {
            "created": 0,
            "reused": 0,
            "expired": 0,
            "errors": 0,
            "current_size": 0,
            "active": 0
        }
        
        # Pre-create minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Pre-create minimum number of connections."""
        for _ in range(self.min_size):
            try:
                conn = self._create_connection()
                if conn:
                    conn_info = ConnectionInfo(
                        connection=conn,
                        created_at=time.time(),
                        last_used=time.time()
                    )
                    self.pool.put(conn_info, block=False)
            except Exception as e:
                logger.warning(f"Failed to pre-create connection for {self.name}: {e}")
    
    def _create_connection(self):
        """Create a new connection."""
        try:
            with self.lock:
                self.total_connections_created += 1
                self.stats["created"] += 1
                self.stats["current_size"] += 1
            
            conn = self.factory()
            logger.debug(f"Created new connection for {self.name} pool")
            return conn
        except Exception as e:
            with self.lock:
                self.stats["errors"] += 1
                self.stats["current_size"] -= 1
            logger.error(f"Failed to create connection for {self.name}: {e}")
            raise
    
    def _is_connection_valid(self, conn_info: ConnectionInfo) -> bool:
        """Check if connection is still valid."""
        now = time.time()
        
        # Check max lifetime
        if now - conn_info.created_at > self.max_lifetime:
            logger.debug(f"Connection exceeded max lifetime in {self.name} pool")
            return False
        
        # Check idle time
        if now - conn_info.last_used > self.max_idle_time:
            logger.debug(f"Connection exceeded max idle time in {self.name} pool")
            return False
        
        return True
    
    def _close_connection(self, conn_info: ConnectionInfo):
        """Close a connection if it has a close method."""
        try:
            if hasattr(conn_info.connection, 'close'):
                conn_info.connection.close()
            elif hasattr(conn_info.connection, 'session') and hasattr(conn_info.connection.session, 'close'):
                conn_info.connection.session.close()
        except Exception as e:
            logger.warning(f"Error closing connection in {self.name} pool: {e}")
        
        with self.lock:
            self.stats["current_size"] -= 1
    
    @contextmanager
    def get_connection(self, timeout: float = 5.0):
        """
        Get a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection
            
        Yields:
            A connection from the pool
        """
        conn_info = None
        start_time = time.time()
        
        try:
            # Try to get from pool
            while True:
                try:
                    # Quick check with short timeout
                    conn_info = self.pool.get(timeout=0.1)
                    
                    # Validate connection
                    if self._is_connection_valid(conn_info):
                        with self.lock:
                            self.stats["reused"] += 1
                            self.active_connections += 1
                            self.stats["active"] = self.active_connections
                        break
                    else:
                        # Connection expired, close it
                        with self.lock:
                            self.stats["expired"] += 1
                        self._close_connection(conn_info)
                        conn_info = None
                        
                except Empty:
                    # Pool is empty, try to create new connection
                    with self.lock:
                        current_total = self.stats["current_size"] + self.active_connections
                        if current_total < self.max_size:
                            # We can create a new connection
                            self.active_connections += 1
                            self.stats["active"] = self.active_connections
                    
                    try:
                        conn = self._create_connection()
                        conn_info = ConnectionInfo(
                            connection=conn,
                            created_at=time.time(),
                            last_used=time.time()
                        )
                        break
                    except Exception as e:
                        with self.lock:
                            self.active_connections -= 1
                            self.stats["active"] = self.active_connections
                        raise RuntimeError(f"Failed to create connection: {e}")
                
                # Check timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Timeout waiting for connection from {self.name} pool")
            
            # Update last used time
            conn_info.last_used = time.time()
            conn_info.use_count += 1
            
            # Yield the connection
            yield conn_info.connection
            
        finally:
            # Return connection to pool
            if conn_info:
                with self.lock:
                    self.active_connections -= 1
                    self.stats["active"] = self.active_connections
                
                # Update last used time
                conn_info.last_used = time.time()
                
                # Try to return to pool
                try:
                    self.pool.put(conn_info, block=False)
                except Full:
                    # Pool is full, close the connection
                    logger.debug(f"Pool {self.name} is full, closing connection")
                    self._close_connection(conn_info)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self.lock:
            return {
                **self.stats,
                "pool_size": self.pool.qsize(),
                "total_created": self.total_connections_created,
                "pool_name": self.name
            }
    
    def clear(self):
        """Clear all connections from pool."""
        cleared = 0
        while not self.pool.empty():
            try:
                conn_info = self.pool.get_nowait()
                self._close_connection(conn_info)
                cleared += 1
            except Empty:
                break
        
        with self.lock:
            self.active_connections = 0
            self.stats["active"] = 0
        
        logger.info(f"Cleared {cleared} connections from {self.name} pool")
        
        # Re-initialize with minimum connections
        self._initialize_pool()
    
    def __del__(self):
        """Clean up pool on deletion."""
        try:
            self.clear()
        except:
            pass

# Pooled client factories
def create_openai_client():
    """Factory for OpenAI clients."""
    from openai import OpenAI
    from config import config
    
    if not config.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    return OpenAI(api_key=config.OPENAI_API_KEY)

def create_pinecone_client():
    """Factory for Pinecone clients."""
    from pinecone import Pinecone
    from config import config
    
    if not config.PINECONE_API_KEY:
        raise ValueError("Pinecone API key not configured")
    
    return Pinecone(api_key=config.PINECONE_API_KEY)

# Global connection pools
openai_pool = ConnectionPool(
    factory=create_openai_client,
    max_size=5,
    min_size=1,
    max_idle_time=300,
    max_lifetime=3600,
    name="OpenAI"
)

pinecone_pool = ConnectionPool(
    factory=create_pinecone_client,
    max_size=3,
    min_size=1,
    max_idle_time=600,
    max_lifetime=7200,
    name="Pinecone"
)

# Helper functions for pooled operations
def embed_with_pool(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Embed texts using pooled OpenAI connection."""
    with openai_pool.get_connection() as client:
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        return [d.embedding for d in response.data]

def search_with_pool(
    index_name: str,
    query_vector: list[float], 
    k: int = 5,
    include_metadata: bool = True
) -> list[tuple]:
    """Search using pooled Pinecone connection."""
    with pinecone_pool.get_connection() as client:
        index = client.Index(index_name)
        results = index.query(
            vector=query_vector,
            top_k=k,
            include_metadata=include_metadata
        )
        return [(m.id, m.metadata) for m in results.matches]

def get_pool_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all pools."""
    return {
        "openai": openai_pool.get_stats(),
        "pinecone": pinecone_pool.get_stats()
    }
