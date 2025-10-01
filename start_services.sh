#!/bin/bash
set -e  # stop if any command fails

echo "Starting Qdrant Docker container..."
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v "D:/Whatsapp Agent/qdrant_storage:/qdrant/storage" \
  qdrant/qdrant

echo "Starting FastAPI server..."
# Activate virtual environment
source .venv/Scripts/activate

# Run FastAPI (async, non-blocking)
uv run uvicorn src.main:app --reload --loop asyncio &
FASTAPI_PID=$!

echo "All services started."
echo "FastAPI PID: $FASTAPI_PID"
