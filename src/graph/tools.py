from typing import List, Dict, Any
from langchain_core.tools import tool

from src.core.settings import settings
from src.graph.state import ChatState
# Assuming you already have qdrant_manager and client_db available
from src.graph.utils.qdrant_db import qdrant_manager
from src.graph.utils.db import client_db, checkpoint_db
from src.core.embeddings import embed_text
from src.core.db_query import (
    SCHEMA_QUERY
)

from src.core.logging_config import get_logger
logger = get_logger(__name__)

def make_vector_search(state: ChatState):
    @tool
    async def _vector_search(query: str) -> List[str]:
        """
        Search the Qdrant vector database for relevant past conversations of this user.
        Args:
            query: The user query
        Returns:
            List of relevant documents
        """
        results = await qdrant_manager.search(query, state["user_id"], embed_text)
        return [r["content"] for r in results]
    return _vector_search

# get schema details
async def _get_schema_details():
    """Fetch schema details """

    query = SCHEMA_QUERY
    try:
        results = await client_db.fetch_all(query, settings.CLIENT_SCHEMA_NAME)

        # Structure the data into JSON format
        structured_data = {}
        
        for row in results:
            table_name = row['table_name']
            column_name = row['column_name']
            
            # Initialize table entry if it doesn't exist
            if table_name not in structured_data:
                structured_data[table_name] = {
                    'table_name': table_name,
                    'columns': []
                }
            
            # Add column details
            column_info = {
                'column_name': column_name,
                'data_type': row['data_type'],
            }
            
            structured_data[table_name]['columns'].append(column_info)
        
        # Convert to list of tables (more standard JSON format)
        final_result = list(structured_data.values())
        
        return final_result

    except Exception as e:
        logger.error(f"Error fetching schema details: {e}")
        raise

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
    

@tool
# get schema details
async def get_schema_details():
    """Fetch schema details """
    return await _get_schema_details()