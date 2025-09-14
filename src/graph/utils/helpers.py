from datetime import datetime
from typing import List, Union
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from sentence_transformers import SentenceTransformer

from src.graph.utils.db import checkpoint_db
from src.core.settings import settings

from src.core.logging_config import get_logger
logger = get_logger(__name__)


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

async def log_conversation(conn, thread_id: str, user_id: str, messages: List[BaseMessage]):
    """Log conversation messages to database with better error handling"""
    if not messages:
        logger.warning(f"No messages to log for thread_id: {thread_id}")
        return
    
    try:
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
                content = msg.content
            elif isinstance(msg, AIMessage):
                role = "bot"
                content = msg.content
            else:
                logger.warning(f"Unknown message type: {type(msg)}")
                continue
                
            await save_message(conn, thread_id, user_id, role, content)
        
        logger.info(f"Logged {len(messages)} messages for thread_id: {thread_id}")
        
    except Exception as e:
        logger.error(f"Error logging conversation for thread_id {thread_id}: {e}")
        raise

async def save_message(conn, thread_id: str, user_id: str, role: str, content: str):
    """Save a single message to database with validation"""
    try:
        # Validate inputs
        if not all([thread_id, user_id, role, content]):
            raise ValueError("All message fields must be provided")
        
        if role not in ["user", "bot"]:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'bot'")
        
        # # Truncate content if too long (adjust limit as needed)
        # max_content_length = 10000
        # if len(content) > max_content_length:
        #     content = content[:max_content_length] + "... [truncated]"
        #     logger.warning(f"Message content truncated for thread_id: {thread_id}")
        
        await conn.execute(
            """
            INSERT INTO messages (thread_id, user_id, role, content, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            """,
            thread_id,
            user_id,
            role,
            content
        )
        
        # logger.debug(f"Saved message: thread_id={thread_id}, role={role}")
        
    except Exception as e:
        # logger.error(f"Error saving message for thread_id {thread_id}: {e}")
        raise

async def get_conversation_history(conn, thread_id: str, limit: int = 50):
    """Retrieve conversation history for a thread"""
    try:
        messages = await conn.fetch(
            """
            SELECT role, content, created_at 
            FROM messages 
            WHERE thread_id = $1 
            ORDER BY created_at ASC 
            LIMIT $2
            """,
            thread_id,
            limit
        )
        
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "created_at": msg["created_at"]
            }
            for msg in messages
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history for thread_id {thread_id}: {e}")
        raise

async def delete_old_messages(conn, days_to_keep: int = 30):
    """Delete messages older than specified days"""
    try:
        result = await conn.execute(
            """
            DELETE FROM messages 
            WHERE created_at < NOW() - INTERVAL '%s days'
            """,
            days_to_keep
        )
        
        # Extract number of deleted rows from result
        deleted_count = int(result.split()[-1]) if result else 0
        logger.info(f"Deleted {deleted_count} old messages (older than {days_to_keep} days)")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error deleting old messages: {e}")
        raise



async def list_threads_for_date(date: str):
    """List all thread IDs for a specific date"""
    query = f"""
        SELECT DISTINCT thread_id 
        FROM checkpoints 
        WHERE thread_id LIKE $1
    """
    date = date.strip()
    try:
        async with checkpoint_db.get_connection() as conn:
            rows = await conn.fetch(query, f"%_{date}")
            logger.info(f"Found {len(rows)} threads for date {date}")
            return [row['thread_id'] for row in rows]
    except Exception as e:
        logger.error(f"Error listing threads for date {date}: {e}")