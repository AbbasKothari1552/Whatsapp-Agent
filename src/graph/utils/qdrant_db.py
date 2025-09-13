import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue

from src.core.settings import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class AsyncQdrantManager:
    """Async Qdrant manager with structured pool-like behavior"""
    def __init__(self, **kwargs):
        self.url = settings.QDRANT_URL
        self.api_key = getattr(settings, "QDRANT_API_KEY", None)
        self.collection_name = getattr(settings, "COLLECTION_NAME", "whatsapp_agent")

        self._client: Optional[AsyncQdrantClient] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Initialize Qdrant connection"""
        async with self._lock:
            if self._client is None:
                try:
                    self._client = AsyncQdrantClient(
                        url=self.url,
                        # api_key=self.api_key
                    )
                    logger.info("Qdrant connection established")

                    # Ensure collection exists
                    await self._ensure_collection()
                except Exception as e:
                    logger.error(f"Failed to connect to Qdrant: {e}")
                    raise
    
    async def close(self):
        """Close connection (Qdrant client does not really need it but kept for symmetry)"""
        async with self._lock:
            if self._client:
                self._client = None
                logger.info("Qdrant connection closed")

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def _ensure_collection(self):
        """Create collection if missing"""
        from qdrant_client.http.models import Distance, VectorParams

        collections = await self._client.get_collections()
        if self.collection_name not in [c.name for c in collections.collections]:
            await self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIM,  # your embedding dimension
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection '{self.collection_name}' created")

    async def save_messages(self, user_id: str, thread_id: str, messages: List[Dict[str, Any]], embed_fn):
        """Save a batch of messages to Qdrant"""
        if not self.is_connected:
            await self.connect()

        points = []
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
            if not content:
                continue
            vector = await embed_fn(content)
            points.append(
                PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "role": role,
                        "content": content,
                        "timestamp": datetime.now(),
                    }
                )
            )

        if points:
            await self._client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"Saved {len(points)} messages for user={user_id}, thread={thread_id}")

    async def search(self, query: str, user_id: str, embed_fn, limit: int = 5):
        """Retrieve most relevant past messages for a user"""
        if not self.is_connected:
            await self.connect()

        query_vector = await embed_fn(query)

        results = await self._client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            )
        )
        return [hit.payload for hit in results]


# Singleton manager
qdrant_manager = AsyncQdrantManager()