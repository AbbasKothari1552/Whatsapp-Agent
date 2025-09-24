from typing import TypedDict, List

class State(TypedDict):
    file_path: str
    extraction_method: str
    extraction_status: str
    doc_text: str
    doc_category: str