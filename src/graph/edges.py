from src.graph.state import ChatState

from src.core.settings import settings

from src.core.logging_config import get_logger
logger = get_logger(__name__)

def file_router(state: ChatState):
    """Route to the correct node based on file type."""
    file = state.get("file")
    if not file:
        return "AnalyzerNode"   # no file → just go to normal assistant flow
    
    # check file extension
    file_lower = file.lower()
    if any(file_lower.endswith(ext) for ext in settings.AUDIO_EXTENSIONS):
        state["file_extension"] = file_lower.split(".")[-1]
        state["is_voice_msg"] = True
        return "VoiceTranscriptionNode"
    # elif any(file_lower.endswith(ext) for ext in settings.IMAGE_EXTENSIONS):
    #     state["file_extension"] = file_lower.split(".")[-1]
    #     state["is_voice_msg"] = False
    #     return "ImageNode"
    else:
        logger.error(f"Unsupported file format: {file}")
        return "AnalyzerNode"   # unsupported file → just go to normal assistant flow


def analyzer_router(state: ChatState):
    if state.get("should_continue"):
        return "assistant"
    return "end"