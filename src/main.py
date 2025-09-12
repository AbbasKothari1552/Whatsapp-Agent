import asyncio
import sys
from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.graph.utils.helpers import log_conversation
from src.core.settings import settings
from src.graph.utils.helpers import (
    get_or_create_thread_id
)

from src.graph.graph import build_graph

app = FastAPI()

@app.on_event("startup")
async def startup():

    # Use the context manager to get the actual saver
    async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
        await saver.setup()


@app.post("/chat/")
async def chat(user_id: str, message: str):
    input_message = [HumanMessage(content=message)]

    thread_id = get_or_create_thread_id(user_id)

    print("thread_id:", thread_id)

    config = {"configurable": {"thread_id": str(thread_id)}}

    # Use the context manager to get the actual saver
    async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
        await saver.setup()
        # Build graph with that saver
        graph = await build_graph(checkpointer=saver)

        response = await graph.ainvoke(
            {"messages": input_message},
            config=config,
        )
        await log_conversation(saver, thread_id, user_id, response["messages"])

    output_message = response["messages"][-1].content

    return {"response": response, "output_message": output_message}


@app.post("/state/")
async def chat(user_id: str):
    thread_id = get_or_create_thread_id(user_id)

    config = {"configurable": {"thread_id": thread_id}}

    # Use the context manager to get the actual saver
    async with AsyncPostgresSaver.from_conn_string(settings.PG_DATABASE_URL) as saver:
        await saver.setup()
        # Build graph with that saver
        graph = await build_graph(checkpointer=saver)

        response = await graph.aget_state(config)

    return response
