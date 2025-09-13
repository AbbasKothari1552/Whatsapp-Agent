from typing import List, Dict, Any
from langchain_core.tools import tool

# Assuming you already have qdrant_manager and client_db available
from src.graph.utils.qdrant_db import qdrant_manager
from src.graph.utils.db import client_db
from src.core.embeddings import embed_text

from src.core.logging_config import get_logger

logger = get_logger(__name__)

@tool
async def vector_search(query: str, user_id: str) -> List[str]:
    """
    Search the Qdrant vector database for relevant past conversations of this user.
    Args:
        query: The user query
        user_id: The unique user identifier
    Returns:
        List of relevant documents
    """
    results = await qdrant_manager.search(query, user_id, embed_text)
    return [r["content"] for r in results]

@tool
async def client_db_query(query: str) -> List[Dict[str, Any]]:
    """
    Query the client database (Postgres for now, Mongo later) for structured company data.
    Args:
        query: The user query (e.g., product name, service, etc.)
    Returns:
        List of records from the client database
    """
    async with client_db.get_connection() as conn:
        rows = await conn.fetch(query)
        return [dict(r) for r in rows]