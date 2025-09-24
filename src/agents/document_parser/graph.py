from langgraph.graph import END, START, StateGraph

from src.agents.document_parser.nodes import (
    parser_agent,
)

from src.agents.document_parser.state import State

from src.core.logging_config import get_logger
logger = get_logger(__name__)

async def document_parser_graph() -> StateGraph:

    graph_builder = StateGraph(State)

    # Add all nodes
    graph_builder.add_node("ParserNode", parser_agent)

    # Define workflow
    graph_builder.add_edge(START, "ParserNode")
    graph_builder.add_edge("ParserNode", END)

    return graph_builder.compile(
        name="DocumentParserGraph",
        )