import asyncio
from sentence_transformers import SentenceTransformer

from src.core.settings import settings

model = SentenceTransformer(settings.EMBEDDING_MODEL)

async def embed_text(text: str):
    # Wrap in asyncio to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: model.encode(text).tolist())
