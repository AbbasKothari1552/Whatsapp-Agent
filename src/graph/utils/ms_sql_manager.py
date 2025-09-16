import asyncio
from contextlib import asynccontextmanager
from typing import Optional
import aioodbc
from urllib.parse import urlparse

from src.core.settings import settings
from src.core.logging_config import get_logger
logger = get_logger(__name__)


class AsyncMSSQLManager:
    """Advanced async SQL Server connection manager with pool support using aioodbc"""

    def __init__(self, **kwargs):
        self.dsn = kwargs.get('dsn')
        self.pool_kwargs = {
            'minsize': kwargs.get('min_size', 1),
            'maxsize': kwargs.get('max_size', 10),
        }
        self._pool: Optional[aioodbc.Pool] = None
        self._pool_lock = asyncio.Lock()

    async def create_pool(self):
        """Create connection pool"""
        async with self._pool_lock:
            if self._pool is None:
                try:
                    self._pool = await aioodbc.create_pool(
                        dsn=self.dsn,
                        autocommit=True,
                        **self.pool_kwargs
                    )
                    logger.info("MSSQL connection pool created")

                    # Test connection
                    async with self._pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SELECT 1")
                            await cur.fetchone()
                    logger.info("MSSQL connection test successful")
                except Exception as e:
                    logger.error(f"Failed to create MSSQL pool: {e}")
                    self._pool = None
                    raise

    async def close_pool(self):
        """Close connection pool"""
        async with self._pool_lock:
            if self._pool:
                try:
                    logger.info("Closing MSSQL connection pool...")
                    self._pool.close()
                    await self._pool.wait_closed()
                    self._pool = None
                    logger.info("MSSQL pool closed successfully")
                except Exception as e:
                    logger.error(f"Error closing MSSQL pool: {e}")

    @property
    def is_pool_active(self) -> bool:
        return self._pool is not None

    @asynccontextmanager
    async def get_connection(self):
        """Context manager to get connection from pool"""
        if not self.is_pool_active:
            await self.create_pool()

        if not self.is_pool_active:
            raise RuntimeError("MSSQL pool is not available")

        conn = None
        try:
            conn = await self._pool.acquire()
            yield conn
        except Exception as e:
            logger.error(f"MSSQL operation error: {e}")
            raise
        finally:
            if conn:
                await self._pool.release(conn)

    @asynccontextmanager
    async def transaction(self):
        """Context manager for MSSQL transactions"""
        async with self.get_connection() as conn:
            try:
                await conn.begin()
                yield conn
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise

    async def execute_query(self, query: str, *args):
        """Execute query (INSERT/UPDATE/DELETE)"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                return cur.rowcount

    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                rows = await cur.fetchall()
                return rows

    async def fetch_one(self, query: str, *args):
        """Fetch single row"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                row = await cur.fetchone()
                return row


# Initialize MSSQL manager for client DB
client_db = AsyncMSSQLManager(
    dsn=settings.MSSQL_DATABASE_DSN,   # e.g. "Driver={ODBC Driver 17 for SQL Server};Server=host;Database=db;UID=user;PWD=pass;"
    min_size=2,
    max_size=20
)
