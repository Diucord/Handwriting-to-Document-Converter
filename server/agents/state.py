from typing import TypedDict


class AgentState(TypedDict):
    """
    LangGraph StateGraph pipeline state schema.

    Flow:
      extract_pages
        → classify_regions
        → render_regions
        → assemble_document
        → END
    """

    # -- input ────────────────────────────────────────────────────────────────────
    images: list[str]                # base64 original base64 image list (PNG)
    messages: list                   # LangChain message history
    export_format: str               # "pdf" (currently pdf only)

    
    # each item: {"page_index": int, "placeholder_index": int, "original_b64": str}
    diagram_regions: list[dict]

    
    # each item: {"page_index", "placeholder_index", "render_strategy", "confidence",
    #           "reason", "original_b64"}
    classified_regions: list[dict]

    
    # each item: {"index": int, "strategy": str, "html_text": str}  — text extraction result
    #      OR: {"index": int, "strategy": str, "base64_png": str}  — image rendering result
    rendered_images: list[dict]

    
    final_pdf_path: str
    final_word_path: str

    # internal — progress tracking (not persisted)
    _conversion_id: str
