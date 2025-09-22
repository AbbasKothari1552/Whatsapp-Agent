from typing import TypedDict, List, Dict, Any, Annotated, Sequence
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Our state is just a list of messages
class ChatState(TypedDict):
    thread_id: str
    user_id: str
    query: str
    file: str
    file_extension: str
    is_voice_msg: bool = False
    voice_msg_transcription: str
    language: str # user preferred language
    should_continue: bool
    response: str
    retrieved_docs: List[str]
    user_data: Dict[str, Any]
    messages: Annotated[Sequence[BaseMessage], add_messages]  # List of messages in the conversation history