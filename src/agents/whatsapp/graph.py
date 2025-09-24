from langgraph.graph import END, START, StateGraph

from src.agents.whatsapp.nodes import (
    analyzer_node,
    assistant_node,
    voice_transcription_node,
    doc_parser_subgraph_node
)
from src.agents.whatsapp.edges import (
    file_router,
    analyzer_router
)
from src.agents.whatsapp.state import ChatState

from src.core.logging_config import get_logger
logger = get_logger(__name__)

async def build_graph(checkpointer) -> StateGraph:

    graph_builder = StateGraph(ChatState)

    # Add all nodes
    graph_builder.add_node("AnalyzerNode", analyzer_node)
    graph_builder.add_node("AssistantNode", assistant_node)
    graph_builder.add_node("VoiceTranscriptionNode", voice_transcription_node)

    # Add sub graph
    graph_builder.add_node("DocParserSubGraph", doc_parser_subgraph_node)

    # Define workflow
    graph_builder.add_conditional_edges(
        START,
        file_router,
        {
            "VoiceTranscriptionNode": "VoiceTranscriptionNode",
            "DocParserSubGraph": "DocParserSubGraph",
            "AnalyzerNode": "AnalyzerNode"
        }
    )
    graph_builder.add_edge("VoiceTranscriptionNode", "AnalyzerNode")
    graph_builder.add_edge("DocParserSubGraph", "AnalyzerNode")
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

