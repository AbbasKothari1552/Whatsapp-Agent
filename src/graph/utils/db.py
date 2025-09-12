import asyncio
import psycopg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.core.settings import settings


async def save_message(pool, thread_id: str, user_id: str, role: str, content: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO messages (thread_id, user_id, role, content, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            """,
            thread_id,
            user_id,
            role,
            content
        )
