import os
import uuid
import aiofiles
import aiohttp
from urllib.parse import urlparse

from src.core.settings import settings
from src.core.logging_config import get_logger
logger = get_logger(__name__)

async def save_file(url: str, folder: str = settings.DATA_DIR) -> dict:
    """
    Download a file from a URL and save it locally with a unique name.
    Returns the local file path.
    """
    logger.info(f"Downloading file: {url} to folder: {folder}")

    os.makedirs(folder, exist_ok=True)

    # Extract path part
    path = urlparse(url).path
    # Get filename
    filename = os.path.basename(path)

    # Join path
    file_path = os.path.join(folder, filename)

    # Download and save asynchronously
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            async with aiofiles.open(file_path, "wb") as out_file:
                async for chunk in response.content.iter_chunked(1024 * 1024):
                    await out_file.write(chunk)

    logger.info(f"File saved to: {file_path}")
    return {"file_path": file_path}
