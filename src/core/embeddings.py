import asyncio
from sentence_transformers import SentenceTransformer
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


model = SentenceTransformer("all-MiniLM-L6-v2")
# # Save it locally wherever you want
# model.save("models/all-MiniLM-L6-v2")

# Load CLIP once
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

async def embed_text(text: str):
    # Wrap in asyncio to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: model.encode(text).tolist())

async def _embed_text(text: str):
    # Wrap in asyncio to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: model.encode(text).tolist())

async def _embed_image(image_input):

    if isinstance(image_input, str):  # file path
        image = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):  # already a PIL Image
        image = image_input
    else:
        raise ValueError("image_input must be a file path or PIL.Image")
    
    inputs = clip_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        image_emb = clip_model.get_image_features(**inputs)

    # Normalize and convert to list for Qdrant
    image_emb = image_emb / image_emb.norm(p=2, dim=-1, keepdim=True)
    return image_emb.squeeze().tolist()
