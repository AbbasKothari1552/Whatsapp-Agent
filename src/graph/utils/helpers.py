from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

from src.graph.utils.db import save_message
from src.core.settings import settings


def get_or_create_thread_id(phone_number: str) -> str:
    """
    Returns a thread_id for the user.
    If daily_reset=True, generates a new thread_id per day.
    """
    return f"{phone_number}_{datetime.now().strftime('%Y-%m-%d')}"

def get_chat_model() -> ChatGroq:
    """Return a ChatGroq model instance."""
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.OPENAI_GPT_120,
        temperature=settings.TEMPERATURE,
    )

async def log_conversation(pool, thread_id: str, user_id: str, results: list[dict]):
    for msg in results:
        if isinstance(msg, HumanMessage):
            role = "user"
            content = msg.content
        else:
            role = "bot"
            content = msg.content
            
        await save_message(pool, thread_id, user_id, role, content)
