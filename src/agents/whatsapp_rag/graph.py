from langgraph.graph import END, START, StateGraph

from src.agents.whatsapp.nodes import (
    analyzer_node,
    assistant_node,
    voice_transcription_node,
    doc_parser_subgraph_node
)
from src.agents.whatsapp_rag.nodes import rag_assistant_node
from src.core.settings import settings
from src.agents.whatsapp.state import ChatState

from src.core.logging_config import get_logger
logger = get_logger(__name__)

def file_router(state: ChatState):
    """Route to the correct node based on file type."""
    file = state.get("file")
    logger.debug(f"Routing based on file: {file}")
    
    # check file extension
    file_lower = file.lower()
    if any(file_lower.endswith(ext) for ext in settings.AUDIO_EXTENSIONS):
        state["file_extension"] = file_lower.split(".")[-1]
        state["is_voice_msg"] = True
        return "VoiceTranscriptionNode"
    else:
        return "RAGAssistantNode"  # default to document parser for other file types

async def build_graph(checkpointer) -> StateGraph:

    graph_builder = StateGraph(ChatState)
    graph_builder.add_node("VoiceTranscriptionNode", voice_transcription_node)
    graph_builder.add_node("RAGAssistantNode", rag_assistant_node)

    # Define workflow
    graph_builder.add_conditional_edges(
        START,
        file_router,
        {
            "VoiceTranscriptionNode": "VoiceTranscriptionNode",
            "RAGAssistantNode": "RAGAssistantNode",
        }
    )
    graph_builder.add_edge("VoiceTranscriptionNode", "RAGAssistantNode")
    graph_builder.add_edge("RAGAssistantNode", END)

    return graph_builder.compile(
        name="ChatGraph",
        checkpointer=checkpointer
        )

