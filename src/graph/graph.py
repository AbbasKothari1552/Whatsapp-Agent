from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.graph.nodes import (
    assistant_node
)

from src.graph.state import ChatState

async def build_graph(checkpointer) -> StateGraph:

    graph_builder = StateGraph(ChatState)

    # Add all nodes
    graph_builder.add_node("assistant", assistant_node)

    # Define workflow
    graph_builder.add_edge(START, "assistant")
    graph_builder.add_edge("assistant", END)

    return graph_builder.compile(checkpointer=checkpointer)