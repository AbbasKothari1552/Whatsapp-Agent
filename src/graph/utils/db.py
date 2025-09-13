import asyncio
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.core.settings import settings

import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlparse

from src.core.logging_config import get_logger
logger = get_logger(__name__)

class AsyncPostgresManager:
    """Advanced async PostgreSQL connection manager with pool support"""
    
    def __init__(self, **kwargs):

        self.dsn =  kwargs.get('dsn')

        # Validate DSN format
        try:
            parsed = urlparse(self.dsn)

            # if not all([parsed.hostname, parsed.username, parsed.path]):
            #     raise ValueError("Invalid database URL format")
        except Exception as e:
            logger.error(f"Invalid database URL: {e}")
            raise

        self.pool_kwargs = {
            'min_size': kwargs.get('min_size', 1),
            'max_size': kwargs.get('max_size', 10),
            'command_timeout': kwargs.get('command_timeout', 60),
        }
        self._pool: Optional[asyncpg.Pool] = None
        self._pool_lock = asyncio.Lock()
    
    async def create_pool(self):
        """Create connection pool"""
        async with self._pool_lock:
            if self._pool is None:
                try:
                    self._pool = await asyncpg.create_pool(
                        self.dsn, 
                        **self.pool_kwargs
                    )
                    logger.info("Database connection pool created")

                    # Test the connection
                    async with self._pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                        logger.info("Database connection test successful")

                except Exception as e:
                    logger.error(f"Failed to create pool: {e}")
                    self._pool = None
                    raise
    
    async def close_pool(self):
        """Close connection pool"""
        async with self._pool_lock:
            if self._pool:
                try:
                    logger.info("Closing database connection pool...")
                    await self._pool.close()
                    self._pool = None
                    logger.info("Database connection pool closed successfully")
                except Exception as e:
                    logger.error(f"Error closing pool: {e}")
    
    @property
    def is_pool_active(self) -> bool:
        """Check if pool is active"""
        return self._pool is not None and not self._pool._closed
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager to get connection from pool"""
        if not self.is_pool_active:
            await self.create_pool()

        if not self.is_pool_active:
            raise RuntimeError("Database pool is not available")
        
        connection = None
        try:
            # Get connection from pool
            connection = await self._pool.acquire()
            yield connection
        except Exception as e:
            logger.error(f"Database operation error: {e}")
            raise
        finally:
            if connection and self._pool and not self._pool._closed:
                try:
                    # Return connection to pool
                    await self._pool.release(connection)
                except Exception as e:
                    logger.error(f"Error releasing connection: {e}")
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        async with self.get_connection() as conn:
            transaction = conn.transaction()
            try:
                await transaction.start()
                yield conn
                await transaction.commit()
            except Exception as e:
                await transaction.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise
    
    async def execute_query(self, query: str, *args):
        """Execute a single query"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Fetch all results from a query"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def fetch_one(self, query: str, *args):
        """Fetch one result from a query"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)


# Initialize the database manager (singleton)
checkpoint_db = AsyncPostgresManager(
    dsn=settings.PG_DATABASE_URL,
    min_size=2,
    max_size=20
)

# Initialize the database manager (singleton)
client_db = AsyncPostgresManager(
    dsn=settings.PG_DATABASE_URL_CLIENT,
    min_size=2,
    max_size=20
)


# Health check function
async def check_database_health():
    """Check database connectivity"""
    try:
        async with client_db.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Database initialization helper
async def init_database_tables():
    """Initialize required database tables"""
    try:
        async with client_db.get_connection() as conn:
            # Create messages table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX (thread_id),
                    INDEX (user_id),
                    INDEX (created_at)
                );
            """)
            
            # Create any other required tables here
            
            logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise