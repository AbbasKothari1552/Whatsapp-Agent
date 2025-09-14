from src.graph.state import ChatState
from langgraph.graph import END

def analyzer_router(state: ChatState):
    if state.get("should_continue"):
        return "assistant"
    return "end"