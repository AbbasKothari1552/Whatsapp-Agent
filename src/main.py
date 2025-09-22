import asyncio
import sys

# Fix psycopg async issue on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.graph.utils.db import checkpoint_db, client_db
from src.graph.utils.qdrant_db import qdrant_manager
from src.core.settings import settings
from src.core.embeddings import embed_text
from src.graph.graph import build_graph
from src.schedular.schedular import start_scheduler

from src.graph.utils.ms_sql_manager import client_db

from src.graph.utils.helpers import (
    get_or_create_thread_id,
    log_conversation,
    get_conversation_history,
)

from src.core.logging_config import get_logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    
    # Startup
    try:
        # Initialize Postgres database pool
        await checkpoint_db.create_pool()

        # # Initialize Postgres database pool
        # await client_db.create_pool()

        # Initialize Qdrant connection
        await qdrant_manager.connect()

        # test
        await client_db.create_pool()

        async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
            await saver.setup()

        # schedulers
        start_scheduler()

        logger.info("Application started successfully")
        yield
        
    finally:      
        # Close database pool
        await checkpoint_db.close_pool()

        # Close qdrant database pool
        await qdrant_manager.close()
        
        print("Application shutdown complete")

app = FastAPI(lifespan=lifespan)


@app.post("/chat/")
async def chat(user_id: str, message: str, file: str = None):
    
    # input_message = [HumanMessage(content=message)]
    thread_id = get_or_create_thread_id(user_id)

    config = {"configurable": {"thread_id": str(thread_id)}}

    initial_state = {
        'thread_id': thread_id,
        'user_id': user_id,
        'query': message,
    }

    if file:
        initial_state['file'] = file

    # Use the context manager to get the actual saver
    async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
        await saver.setup()
        # Build graph with that saver
        graph = await build_graph(checkpointer=saver)

        response = await graph.ainvoke(
            initial_state,
            config=config,
        )

    # # Log conversation using transaction
    # async with checkpoint_db.transaction() as conn:
    #     await log_conversation(conn, thread_id, user_id, response["messages"])

    # # Embed and store log conversation
    # await qdrant_manager.save_messages(
    #     user_id=user_id,
    #     thread_id=thread_id,
    #     messages=response["messages"],
    #     embed_fn=embed_text
    # )

    output_message = response.get("response")

    return {"response": response, "output_message": output_message}


@app.post("/state/")
async def chat(user_id: str):
    
    thread_id = get_or_create_thread_id(user_id)
    config = {"configurable": {"thread_id": "2022_2025-09-13"}}

    # Use the context manager to get the actual saver
    async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
        # Build graph with that saver
        graph = await build_graph(checkpointer=saver)
        response = await graph.aget_state(config)

    # # seach vector db
    # vector_response = await qdrant_manager.search(
    #     query="what is my name?",
    #     user_id=user_id,
    #     embed_fn=embed_text
    # )

    return {"response": response}
