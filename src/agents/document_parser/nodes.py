import os
import json
import asyncio

from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.document_parser.state import State
from src.agents.document_parser.tools import (
    extract_docx_text, 
    extract_excel_text, 
    extract_image_text, 
    extract_pdf_text
    )
from src.core.prompts import (
     DOC_ANALYZER_SYSTEM_PROMPT,
     DOC_ANALYZER_HUMAN_PROMPT
)
from src.utils.helpers import (
    get_chat_model
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
        
async def doc_analyzer_node(state: State) -> State:
    """Analyze extracted document text and summarize key points."""
    logger.info("Starting Document Analyzer Node.")

    doc_text = state.get("doc_text")
    if not doc_text:
        logger.warning("No document text available for analysis.")
        return state
    
    model = get_chat_model()

    messages = [
         SystemMessage(content=DOC_ANALYZER_SYSTEM_PROMPT),
         HumanMessage(content=DOC_ANALYZER_HUMAN_PROMPT.format(doc_text=doc_text)),
    ]

    try:
        # call LLM
        response = await model.ainvoke(messages)
    except Exception as e:
        logger.error(f"Error in doc_analyzer_node LLM call: {e}")

    try:
        # Parse JSON response
        content = json.loads(response.content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error parsing JSON response in doc_analyzer_node: {e}")
    
    state['doc_category'] = content.get("doc_category")
    state['should_continue'] = content.get("should_continue")
    state['products'] = content.get("products", [])
    if content.get("response"):
        state["response"] = content.get("response", "")

    logger.info("Document analysis completed successfully.")
    return state