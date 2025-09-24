import os
import asyncio

from src.agents.document_parser.state import State
from src.agents.document_parser.tools import (
    extract_docx_text, 
    extract_excel_text, 
    extract_image_text, 
    extract_pdf_text
    )

from src.core.logging_config import get_logger
logger = get_logger(__name__)

# Helper function
def get_extractor(filepath: str):
        """Get appropriate extractor based on file type"""
        logger.info(f"Getting extractor for file: {filepath}")

        # Split the path into root and extension
        _, ext = os.path.splitext(filepath)
        file_type = ext[1:].lower() if ext else ''  # Remove the dot and convert to lower case

        if file_type == "pdf":
            return extract_pdf_text
        elif file_type in ["doc", "docx"]:
            return extract_docx_text
        elif file_type in ["xls", "xlsx"]:
            return extract_excel_text
        elif file_type in ["jpg", "jpeg", "png", "tiff"]:
            return extract_image_text
        return None


async def parser_agent(state: State) -> State:
        """Main extraction method"""
        logger.info(f"Starting Parser Agent.")

        # get file path
        file_path = state.get("file_path")

        # get extractor 
        extractor = get_extractor(file_path)
        if not extractor:
            logger.warning(f"No extractor available for file: {file_path}")
            state["extraction_status"] = "failed"
            return state
        
        try:
            result = await asyncio.to_thread(
                extractor,
                input_path=file_path
            )

            # Update the existing state object instead of returning a new one
            state["doc_text"] = result.get("text")
            state["extraction_method"] = result.get("method")
            state["extraction_status"] = "success"

            logger.info(f"Extraction completed for file: {file_path}")

            return state

        except Exception as e:
            logger.error(f"Extraction failed for {file_path}: {str(e)}")

            state["extraction_status"] = "failed"
            return state