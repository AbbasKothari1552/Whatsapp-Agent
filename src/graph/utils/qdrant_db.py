import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams

from src.core.settings import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class AsyncQdrantManager:
    """Async Qdrant manager with structured pool-like behavior"""
    def __init__(self, **kwargs):
        self.url = settings.QDRANT_URL
        self.api_key = getattr(settings, "QDRANT_API_KEY", None)
        self._client: Optional[AsyncQdrantClient] = None
        self._lock = asyncio.Lock()

        # Registry of collections: define all configs here
        self.collections_config = settings.COLLECTIONS_CONFIG

    async def connect(self):
        """Initialize Qdrant connection"""
        async with self._lock:
            if self._client is None:
                try:
                    self._client = AsyncQdrantClient(
                        url=self.url,
                        # api_key=self.api_key
                    )
                    # Ensure all collections exist
                    for name, cfg in self.collections_config.items():
                        await self._ensure_collection(name, cfg["dim"], cfg["distance"])
                    logger.info("Qdrant connection established")

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

    async def _ensure_collection(self, collection_name: str, dim: int, distance):
        """Create collection if missing"""
        collections = await self._client.get_collections()
        if collection_name not in [c.name for c in collections.collections]:
            await self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dim,  # your embedding dimension
                    distance=distance
                )
            )
            logger.info(f"Collection '{collection_name}' created")

    # ------------------ SAVE ------------------
    async def save_messages(self, user_id: str, thread_id: str, messages, collection_name="whatsapp_agent"):
        """Save human/AI conversation"""
        if not self.is_connected:
            await self.connect()

        cfg = self.collections_config[collection_name]
        embed_fn = cfg["embed_fn"]
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
            await self._client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Saved {len(points)} messages for user={user_id}, thread={thread_id}")

    async def save_image(self, image_id: str, image_url: str, image_array, collection_name="image_products"):
        """Save product image embedding"""
        if not self.is_connected:
            await self.connect()

        cfg = self.collections_config[collection_name]
        embed_fn = cfg["embed_fn"]
        vector = await embed_fn(image_array)
        point = PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={
                "image_id": image_id,
                "image_url": image_url,
            }
        )
        await self._client.upsert(collection_name=collection_name, points=[point])
        logger.info(f"Saved image embedding for image_id={image_id}")


    # ------------------ SEARCH ------------------
    async def search_messages(self, query: str, user_id: str, limit=5, collection_name="whatsapp_agent"):
        """Retrieve most relevant past messages for a user"""
        if not self.is_connected:
            await self.connect()
        
        cfg = self.collections_config[collection_name]
        query_vector = await cfg["embed_fn"](query)

        results = await self._client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            )
        )
        return [hit.payload for hit in results]

    async def search_image(self, image_array, limit=3, collection_name="image_products"):
        """Find similar product images"""
        if not self.is_connected:
            await self.connect()

        cfg = self.collections_config[collection_name]
        query_vector = await cfg["embed_fn"](image_array)
        
        results = await self._client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
        )
        return [
            {
                "payload": hit.payload,
                "score": hit.score
            } 
            for hit in results
        ]


# Singleton manager
qdrant_manager = AsyncQdrantManager()