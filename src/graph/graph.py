from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.graph.nodes import (
    assistant_node,
    analyzer_node,
)

from src.graph.state import ChatState

async def build_graph(checkpointer) -> StateGraph:

    graph_builder = StateGraph(ChatState)

    # Add all nodes
    graph_builder.add_node("AnalyzerNode", analyzer_node)

    # Define workflow
    graph_builder.add_edge(START, "AnalyzerNode")
    graph_builder.add_edge("AnalyzerNode", END)

    return graph_builder.compile(
        name="ChatGraph",
        checkpointer=checkpointer
        )