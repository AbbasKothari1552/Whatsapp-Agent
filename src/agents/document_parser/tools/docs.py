from docx import Document
from typing import Dict
from pathlib import Path

from langsmith import traceable

from src.core.logging_config import get_logger
logger = get_logger(__name__)

@traceable(name="Docx Parser")
def extract_docx_text(input_path: str) -> Dict:
    """Extract text from DOCX files"""
    logger.info(f"Extracting docx file...")
    try:
        doc = Document(input_path)
        text = "\n".join([para.text for para in doc.paragraphs])

        logger.debug(f"Extracted text: {text}")

        return {
            "content_type": "text",
            "method": "python-docx",
            "word_count": len(text.split()),
            "text": text
        }
    except Exception as e:
        logger.error(f"Failed to extract content from docx: {str(e)}", exc_info=True)
        raise Exception(f"DOCX extraction failed: {str(e)}")
    