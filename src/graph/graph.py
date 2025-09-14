from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.graph.nodes import (
    analyzer_node,
    assistant_node,
)
from src.graph.edges import (
    analyzer_router
)

from src.graph.state import ChatState

async def build_graph(checkpointer) -> StateGraph:

    graph_builder = StateGraph(ChatState)

    # Add all nodes
    graph_builder.add_node("AnalyzerNode", analyzer_node)
    graph_builder.add_node("AssistantNode", assistant_node)

    # Define workflow
    graph_builder.add_edge(START, "AnalyzerNode")
    # graph_builder.add_edge("AnalyzerNode", END)
    graph_builder.add_conditional_edges(
        "AnalyzerNode",
        analyzer_router,
        {
            "assistant": "AssistantNode",
            "end": END
        }

    )
    graph_builder.add_edge("AssistantNode", END)

    return graph_builder.compile(
        name="ChatGraph",
        checkpointer=checkpointer
        )

