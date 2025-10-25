"""Thread-safe connection pool for database adapters.

This module provides a comprehensive connection pooling system that prevents
memory leaks by properly managing database connections across multiple threads.
It includes connection health checks, automatic cleanup of idle connections,
and thread-safe operations.
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict
from queue import Queue, Empty
from typing import Any, Dict, Optional, Union
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PooledConnection:
    """Wrapper for pooled connections with metadata."""
    
    def __init__(self, connection, created_at: float, last_used: float):
        self.connection = connection
        self.created_at = created_at
        self.last_used = last_used
        self.in_use = False
        self.usage_count = 0
        
    def mark_used(self):
        """Mark connection as used and update metadata."""
        self.last_used = time.time()
        self.usage_count += 1
        self.in_use = True
        
    def mark_returned(self):
        """Mark connection as returned to pool."""
        self.in_use = False

class ConnectionPoolManager:
    """Thread-safe connection pool for database adapters.
    
    This class manages connection pools for different types of database adapters
    (SQLite, LanceDB, Kuzu) with features like:
    - Thread-safe operations
    - Connection health checks
    - Automatic cleanup of idle connections
    - Connection limits and timeout handling
    """
    
    def __init__(self, 
                 max_connections_per_type: int = 10,
                 max_idle_time: int = 300,  # 5 minutes
                 connection_timeout: int = 30):
        """Initialize the connection pool manager.
        
        Args:
            max_connections_per_type: Maximum number of connections per adapter type
            max_idle_time: Maximum time a connection can be idle before cleanup
            connection_timeout: Timeout for getting a connection from the pool
        """
        self._pools: Dict[str, Queue] = {
            'sqlite': Queue(maxsize=max_connections_per_type),
            'lancedb': Queue(maxsize=max_connections_per_type),
            'kuzu': Queue(maxsize=max_connections_per_type)
        }
        self._lock = threading.RLock()
        self._connection_count = defaultdict(int)
        self._max_idle_time = max_idle_time
        self._connection_timeout = connection_timeout
        self._cleanup_thread = None
        self._shutdown = False
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start background thread for cleaning up idle connections."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_idle_connections,
            daemon=True,
            name="ConnectionPool-Cleanup"
        )
        self._cleanup_thread.start()
        logger.info("Connection pool cleanup thread started")
        
    async def get_connection(self, adapter_type: str, **kwargs) -> PooledConnection:
        """Get a connection from the pool or create a new one.
        
        Args:
            adapter_type: Type of adapter ('sqlite', 'lancedb', 'kuzu')
            **kwargs: Arguments to pass to connection creation
            
        Returns:
            PooledConnection: A wrapped connection with metadata
            
        Raises:
            ValueError: If adapter type is unsupported
            Exception: If maximum connections are reached
        """
        if adapter_type not in self._pools:
            raise ValueError(f"Unsupported adapter type: {adapter_type}")
            
        pool = self._pools[adapter_type]
        
        try:
            # Try to get existing connection from pool
            pooled_conn = pool.get(timeout=self._connection_timeout)
            
            # Validate connection is still alive
            if self._is_connection_alive(pooled_conn.connection, adapter_type):
                pooled_conn.mark_used()
                logger.debug(f"Reusing {adapter_type} connection (usage: {pooled_conn.usage_count})")
                return pooled_conn
            else:
                # Connection is dead, create new one
                logger.warning(f"Dead {adapter_type} connection found, creating new one")
                await self._close_connection(pooled_conn.connection, adapter_type)
                
        except Empty:
            # No available connections, create new one if under limit
            with self._lock:
                if self._connection_count[adapter_type] < pool.maxsize:
                    self._connection_count[adapter_type] += 1
                else:
                    # If we've reached the limit, create a new connection that won't be pooled
                    # This allows the system to continue working even when the pool is full
                    logger.warning(f"Connection pool limit reached for {adapter_type}, creating unpooled connection")
        
        # Create new connection
        connection = await self._create_connection(adapter_type, **kwargs)
        pooled_conn = PooledConnection(
            connection=connection,
            created_at=time.time(),
            last_used=time.time()
        )
        pooled_conn.mark_used()
        
        logger.info(f"Created new {adapter_type} connection (total: {self._connection_count[adapter_type]})")
        return pooled_conn
        
    async def return_connection(self, adapter_type: str, pooled_conn: PooledConnection):
        """Return a connection to the pool.
        
        Args:
            adapter_type: Type of adapter
            pooled_conn: The pooled connection to return
        """
        if not pooled_conn or not pooled_conn.connection:
            return
            
        try:
            pooled_conn.mark_returned()
            self._pools[adapter_type].put(pooled_conn, timeout=5)
            logger.debug(f"Returned {adapter_type} connection to pool")
        except Exception as e:
            # Pool is full or other error, close the connection
            logger.warning(f"Failed to return {adapter_type} connection to pool: {e}")
            await self._close_connection(pooled_conn.connection, adapter_type)
            with self._lock:
                self._connection_count[adapter_type] -= 1
                
    async def _create_connection(self, adapter_type: str, **kwargs):
        """Create a new database connection.
        
        Args:
            adapter_type: Type of adapter to create
            **kwargs: Arguments for connection creation
            
        Returns:
            Database connection instance
        """
        # Import here to avoid circular imports
        if adapter_type == 'sqlite':
            from grizabella.db_layers.sqlite.sqlite_adapter import SQLiteAdapter
            return SQLiteAdapter(**kwargs)
        elif adapter_type == 'lancedb':
            from grizabella.db_layers.lancedb.lancedb_adapter import LanceDBAdapter
            return LanceDBAdapter(**kwargs)
        elif adapter_type == 'kuzu':
            from grizabella.db_layers.kuzu.thread_safe_kuzu_adapter import ThreadSafeKuzuAdapter
            return ThreadSafeKuzuAdapter(**kwargs)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
            
    async def _close_connection(self, connection, adapter_type: str):
        """Close a database connection.
        
        Args:
            connection: The connection to close
            adapter_type: Type of adapter for logging
        """
        try:
            if hasattr(connection, 'close'):
                if asyncio.iscoroutinefunction(connection.close):
                    await connection.close()
                else:
                    connection.close()
            logger.debug(f"Closed {adapter_type} connection")
        except Exception as e:
            logger.error(f"Error closing {adapter_type} connection: {e}")
            
    def _is_connection_alive(self, connection, adapter_type: str) -> bool:
        """Check if a connection is still alive.
        
        Args:
            connection: The connection to check
            adapter_type: Type of adapter
            
        Returns:
            True if connection is alive, False otherwise
        """
        try:
            if adapter_type == 'sqlite':
                return hasattr(connection, 'conn') and connection.conn is not None
            elif adapter_type == 'lancedb':
                return hasattr(connection, '_db') and connection._db is not None
            elif adapter_type == 'kuzu':
                return hasattr(connection, 'conn') and connection.conn is not None
            return False
        except Exception:
            return False
            
    def _cleanup_idle_connections(self):
        """Background thread to clean up idle connections."""
        while not self._shutdown:
            try:
                current_time = time.time()
                for adapter_type, pool in self._pools.items():
                    temp_connections = []
                    
                    # Drain pool and check each connection
                    while not pool.empty():
                        try:
                            pooled_conn = pool.get_nowait()
                            if (current_time - pooled_conn.last_used > self._max_idle_time and 
                                not pooled_conn.in_use):
                                # Connection is idle and not in use, close it
                                asyncio.create_task(
                                    self._close_connection(pooled_conn.connection, adapter_type)
                                )
                                with self._lock:
                                    self._connection_count[adapter_type] -= 1
                                logger.info(f"Cleaned up idle {adapter_type} connection")
                            else:
                                temp_connections.append(pooled_conn)
                        except Empty:
                            break
                            
                    # Put valid connections back in pool
                    for conn in temp_connections:
                        pool.put(conn)
                        
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
                
            # Sleep for 1 minute before next cleanup
            time.sleep(60)
            
    async def cleanup_all(self):
        """Clean up all connections in the pool."""
        self._shutdown = True
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
            
        for adapter_type, pool in self._pools.items():
            while not pool.empty():
                try:
                    pooled_conn = pool.get_nowait()
                    await self._close_connection(pooled_conn.connection, adapter_type)
                except Empty:
                    break
                    
        with self._lock:
            self._connection_count.clear()
            
        logger.info("All connection pools cleaned up")
        
    def close_all_pools(self):
        """Synchronous method to close all connection pools."""
        import asyncio
        try:
            # Run the async cleanup in a new event loop if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.cleanup_all())
            loop.close()
        except Exception as e:
            logger.error(f"Error closing all pools: {e}")
            
    @asynccontextmanager
    async def get_connection_context(self, adapter_type: str, **kwargs):
        """Context manager for getting and returning connections.
        
        Args:
            adapter_type: Type of adapter
            **kwargs: Arguments for connection creation
            
        Yields:
            Database connection instance
        """
        pooled_conn = None
        try:
            pooled_conn = await self.get_connection(adapter_type, **kwargs)
            yield pooled_conn.connection
        finally:
            if pooled_conn:
                await self.return_connection(adapter_type, pooled_conn)
                
    def get_pool_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about connection pools.
        
        Returns:
            Dictionary with pool statistics
        """
        stats = {}
        for adapter_type, pool in self._pools.items():
            stats[adapter_type] = {
                'pool_size': pool.qsize(),
                'max_size': pool.maxsize,
                'active_connections': self._connection_count[adapter_type],
                'available_connections': pool.qsize()
            }
        return stats

# Global singleton instance
_connection_pool_manager: Optional[ConnectionPoolManager] = None
_pool_lock = threading.Lock()

def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager instance.
    
    Returns:
        ConnectionPoolManager: The singleton instance
    """
    global _connection_pool_manager
    if _connection_pool_manager is None:
        with _pool_lock:
            if _connection_pool_manager is None:
                _connection_pool_manager = ConnectionPoolManager()
    return _connection_pool_manager

def cleanup_global_connection_pool():
    """Clean up the global connection pool manager."""
    global _connection_pool_manager
    if _connection_pool_manager is not None:
        # This should be called from an async context
        # For now, we'll create a task to handle cleanup
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_connection_pool_manager.cleanup_all())
            else:
                loop.run_until_complete(_connection_pool_manager.cleanup_all())
        except Exception as e:
            logger.error(f"Error cleaning up global connection pool: {e}")
        finally:
            _connection_pool_manager = None