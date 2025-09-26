from langgraph.graph import END, START, StateGraph

from src.agents.document_parser.nodes import (
    parser_agent,
    doc_analyzer_node
)

from src.agents.document_parser.state import State

from src.core.logging_config import get_logger
logger = get_logger(__name__)

async def document_parser_graph() -> StateGraph:

    graph_builder = StateGraph(State)

    # Add all nodes
    graph_builder.add_node("ParserNode", parser_agent)
    graph_builder.add_node("DocAnalyzerNode", doc_analyzer_node)

    # Define workflow
    graph_builder.add_edge(START, "ParserNode")
    graph_builder.add_edge("ParserNode", "DocAnalyzerNode")
    graph_builder.add_edge("DocAnalyzerNode", END)

    return graph_builder.compile(
        name="DocumentParserGraph",
    )