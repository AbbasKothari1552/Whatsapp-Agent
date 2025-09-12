
from src.graph.utils.helpers import (
    get_chat_model
)

from src.graph.state import ChatState

async def assistant_node(state: ChatState) -> ChatState:
    model = get_chat_model()

    response = await model.ainvoke(state["messages"])
    
    return {"messages": response}