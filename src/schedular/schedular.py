import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.graph.graph import build_graph
from src.core.settings import settings
from src.graph.utils.qdrant_db import qdrant_manager
from src.core.embeddings import embed_text
from src.core.logging_config import get_logger

from src.graph.utils.helpers import (
    list_threads_for_date
)

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def flush_yesterday_threads():
    """Fetch all yesterday's threads from LangGraph checkpointer and archive to Qdrant"""
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
            # TODO: Implement actual listing of thread_ids from saver storage
            thread_ids = await list_threads_for_date(yesterday)

            # Build graph with that saver
            graph = await build_graph(checkpointer=saver)

            for thread_id in thread_ids:

                config={"configurable": {"thread_id": thread_id}}

                state = await graph.aget_state(config)

                messages = state[0].get("messages", [])

                if not messages:
                    continue

                user_id = thread_id.split("_")[0]  # since format = <user_id>_<date>

                # Save all messages to Qdrant
                await qdrant_manager.save_messages(
                    user_id=user_id,
                    thread_id=thread_id,
                    messages=messages,
                    embed_fn=embed_text,
                )

                logger.info(f"Flushed {len(messages)} messages for thread={thread_id} to Qdrant")

    except Exception as e:
        logger.error(f"Error while flushing yesterday's threads: {e}")


def start_scheduler():
    scheduler.add_job(
        flush_yesterday_threads, 
        "cron", 
        hour=9, 
        minute=15,
        misfire_grace_time=3600,  # 1 hour grace period
        )
    scheduler.start()
    logger.info("Scheduler started - flushing job set for 09:10 daily")
