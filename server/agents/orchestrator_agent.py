"""
orchestrator_agent.py — LangGraph StateGraph pipeline.

Flow:
  extract_pages      — tool_extract_html call (per-page)
    → classify_regions — tool_classify_image call (per-placeholder)
    → render_regions   — tool_render_* call (per-strategy)
    → assemble_document — tool_assemble_pdf call
    → END
"""

import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.graph import StateGraph, END
from agents.state import AgentState

# Max parallel API calls per step (avoid rate limits)
_MAX_WORKERS = 4

from tools.tool_extract_html import extract_html
from tools.tool_classify_image import classify_image
from tools.tool_render_mermaid import render_mermaid
from tools.tool_render_chartjs import render_chartjs
from tools.tool_render_illustration import render_illustration
from tools.tool_render_math import render_math
from tools.tool_preserve_original import preserve_original
from tools.tool_assemble_pdf import assemble_pdf

logger = logging.getLogger(__name__)


# --- utils ────────────────────────────────────────────────────────────────────

_PLACEHOLDER_RE = re.compile(r"\[IMAGE_PLACE_HOLDER_(\d+)\]")



def _replace_placeholders(
    html_text: str,
    page_index: int,
    region_results: dict[tuple[int, int], str],
    bbox_info: dict[tuple[int, int], dict] | None = None,
) -> str:
    """Replace [IMAGE_PLACE_HOLDER_N] with inline <img>."""
    # A4 body width ≈ 180mm at 15mm margins → ~560px at 96dpi
    BODY_WIDTH = 560

    def _repl(match: re.Match) -> str:
        ph_idx = int(match.group(1))
        b64 = region_results.get((page_index, ph_idx))
        if b64 is None:
            return match.group(0)  # not processed yet, keep placeholder
        if b64 == "":
            return ""  # text_only: remove placeholder entirely

        # Use original bbox width proportion for natural sizing
        max_w = BODY_WIDTH  # default full width
        bbox = (bbox_info or {}).get((page_index, ph_idx))
        if bbox and bbox.get("width_pct"):
            # Scale to body width based on how much of the page width the region occupied
            max_w = max(200, min(BODY_WIDTH, int(BODY_WIDTH * bbox["width_pct"] / 100)))

        return (
            f'<figure style="text-align:center;margin:16px 0;">'
            f'<img src="data:image/png;base64,{b64}" '
            f'style="max-width:{max_w}px;height:auto;'
            f'display:block;margin:0 auto;object-fit:contain;" '
            f'alt="diagram-{page_index}-{ph_idx}">'
            f'</figure>'
        )
    return _PLACEHOLDER_RE.sub(_repl, html_text or "")


def _normalize_strategy(strategy: str) -> str:
    s = (strategy or "").strip()
    if s in ("illustration_redraw", "illustration"):
        return "illustration_redraw"
    if s in ("math_graph",):
        return "math_graph"
    if s in ("mermaid", "chartjs", "text_only"):
        return s
    if s == "preserve_original":
        return "preserve_original"
    # 알 수 없는 전략 → illustration_redraw (preserve_original 아님)
    return "illustration_redraw"


# ═════════════════════════════════════════════════════════════════════════════
# Node 1: extract_pages
# ═════════════════════════════════════════════════════════════════════════════

def _extract_single_page(page_idx: int, img_b64: str):
    """Extract a single page — runs in thread pool."""
    result = extract_html.invoke({"image_b64": img_b64, "index": page_idx})
    html_text = (result.get("html_text") or "").strip()
    if not html_text or result.get("strategy") == "preserve_original":
        raise ValueError("extract returned empty or preserve_original")
    return page_idx, img_b64, result


def extract_pages_via_tool(state: AgentState) -> dict:
    """Call extract_html tool per-page (parallel)."""
    cid = state.get("_conversion_id", "")
    images = state.get("images", [])
    rendered_images: list[dict] = []
    diagram_regions: list[dict] = []
    total = len(images)

    if cid:
        set_progress(cid, 0, f"텍스트 추출 중... (0/{total})", stage="extract")

    # Parallel extraction
    page_results: dict[int, tuple] = {}  # page_idx -> (img_b64, result) or None for failures
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {
            pool.submit(_extract_single_page, idx, b64): idx
            for idx, b64 in enumerate(images)
        }
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            page_idx = futures[future]
            if cid:
                pct = int((done_count / max(total, 1)) * 25)
                set_progress(cid, pct, f"텍스트 추출 중... ({done_count}/{total})", stage="extract")
                set_stage_detail(cid, done_count, total)
            try:
                page_idx, img_b64, result = future.result()
                page_results[page_idx] = (img_b64, result)
            except Exception as e:
                logger.warning("[extract] page=%s failed (%s) -> preserve_original", page_idx, e)
                page_results[page_idx] = None

    # Assemble results in page order
    for page_idx in range(total):
        entry = page_results.get(page_idx)
        if entry is None:
            fallback = preserve_original.invoke({
                "image_b64": images[page_idx],
                "index": page_idx,
            })
            rendered_images.append(fallback)
            continue

        img_b64, result = entry
        html_text = (result.get("html_text") or "").strip()
        placeholder_indices = result.get("placeholder_indices", [])

        rendered_images.append({
            "index": page_idx,
            "strategy": "html_css",
            "html_text": html_text,
        })

        placeholder_images = result.get("placeholder_images", {})
        placeholder_bboxes = result.get("placeholder_bboxes", {})
        for ph_idx in placeholder_indices:
            cropped_b64 = placeholder_images.get(str(ph_idx), img_b64)
            bbox = placeholder_bboxes.get(str(ph_idx))
            diagram_regions.append({
                "page_index": page_idx,
                "placeholder_index": ph_idx,
                "original_b64": cropped_b64,
                "bbox": bbox,
            })

        logger.info(
            "[extract] page=%s html_len=%s placeholders=%s",
            page_idx, len(html_text), len(placeholder_indices),
        )

    return {
        "rendered_images": rendered_images,
        "diagram_regions": diagram_regions,
        "classified_regions": [],
        "final_pdf_path": "",
        "final_word_path": "",
    }


# ═════════════════════════════════════════════════════════════════════════════
# Node 2: classify_and_render (merged for speed)
# ═════════════════════════════════════════════════════════════════════════════

def _classify_and_render_single(region: dict) -> tuple[int, int, str, str, dict | None]:
    """Classify + render a single region in one shot — runs in thread pool.

    For illustration_redraw: the GPT-4o analysis inside render_illustration
    already acts as classification (it can return text_only).
    For other strategies: classify first, then dispatch to the appropriate renderer.

    Returns: (page_idx, ph_idx, b64_result, strategy, bbox)
    """
    page_idx = region["page_index"]
    ph_idx = region["placeholder_index"]
    original_b64 = region.get("original_b64", "")
    bbox = region.get("bbox")

    # Step 1: Classify
    cls_result = classify_image.invoke({
        "image_b64": original_b64,
        "page_index": page_idx,
        "placeholder_index": ph_idx,
    })
    strategy = _normalize_strategy(cls_result.get("render_strategy", "preserve_original"))

    logger.info(
        "[classify+render] page=%s ph=%s -> %s (%s)",
        page_idx, ph_idx, strategy, cls_result.get("confidence"),
    )

    # Step 2: Render based on strategy
    if strategy == "text_only":
        return page_idx, ph_idx, "", strategy, bbox

    if strategy == "math_graph":
        out = render_math.invoke({"image_b64": original_b64, "index": page_idx})
    elif strategy == "mermaid":
        out = render_mermaid.invoke({"image_b64": original_b64, "index": page_idx})
    elif strategy == "chartjs":
        out = render_chartjs.invoke({"image_b64": original_b64, "index": page_idx})
    elif strategy == "illustration_redraw":
        out = render_illustration.invoke({"image_b64": original_b64, "index": page_idx})
        # render_illustration may internally decide text_only
        if (out or {}).get("strategy") == "text_only":
            return page_idx, ph_idx, "", "text_only", bbox
    else:
        out = preserve_original.invoke({"image_b64": original_b64, "index": page_idx})

    b64 = (out or {}).get("base64_png", "") or original_b64
    return page_idx, ph_idx, b64, strategy, bbox


def classify_and_render_via_tool(state: AgentState) -> dict:
    """Classify + render all regions in parallel (merged pipeline)."""
    cid = state.get("_conversion_id", "")
    rendered_images = list(state.get("rendered_images", []))
    diagram_regions = state.get("diagram_regions", [])

    if not diagram_regions:
        if cid:
            set_progress(cid, 85, "렌더링할 시각 요소 없음", stage="render")
        return {"rendered_images": rendered_images, "classified_regions": []}

    region_results: dict[tuple[int, int], str] = {}
    bbox_info: dict[tuple[int, int], dict] = {}
    total = len(diagram_regions)

    if cid:
        set_progress(cid, 25, f"시각 요소 처리 중... (0/{total})", stage="classify")

    # Parallel classify + render
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {
            pool.submit(_classify_and_render_single, region): i
            for i, region in enumerate(diagram_regions)
        }
        done_count = 0
        for future in as_completed(futures):
            idx = futures[future]
            done_count += 1
            if cid:
                pct = 25 + int((done_count / max(total, 1)) * 60)
                set_progress(cid, pct, f"시각 요소 처리 중... ({done_count}/{total})", stage="render")
                set_stage_detail(cid, done_count, total)
            try:
                page_idx, ph_idx, b64, strategy, bbox = future.result()
                region_results[(page_idx, ph_idx)] = b64
                if bbox:
                    bbox_info[(page_idx, ph_idx)] = bbox
                logger.info("[render] page=%s ph=%s strategy=%s ok", page_idx, ph_idx, strategy)
            except Exception as e:
                region = diagram_regions[idx]
                page_idx = region["page_index"]
                ph_idx = region["placeholder_index"]
                original_b64 = region.get("original_b64", "")
                logger.warning("[render] page=%s ph=%s failed: %s -> preserve_original", page_idx, ph_idx, e)
                fb = preserve_original.invoke({"image_b64": original_b64, "index": page_idx})
                region_results[(page_idx, ph_idx)] = (fb or {}).get("base64_png", original_b64)
                bbox = region.get("bbox")
                if bbox:
                    bbox_info[(page_idx, ph_idx)] = bbox

    for item in rendered_images:
        html_text = item.get("html_text")
        if not html_text:
            continue
        item["html_text"] = _replace_placeholders(html_text, item["index"], region_results, bbox_info)

    return {"rendered_images": rendered_images, "classified_regions": []}

# ═════════════════════════════════════════════════════════════════════════════
# Node 4: assemble_document
# ═════════════════════════════════════════════════════════════════════════════

def assemble_document_via_tool(state: AgentState) -> dict:
    """
    tool_assemble_pdf call.
    Tool signature: assemble_pdf(rendered_images: list[dict], output_path: str) -> str
    """
    cid = state.get("_conversion_id", "")
    if cid:
        set_progress(cid, 90, "PDF 문서 조립 중...", stage="assemble")

    rendered_images = state.get("rendered_images", [])
    pdf_path = assemble_pdf.invoke({"rendered_images": rendered_images, "output_path": ""})

    if cid:
        set_progress(cid, 98, "PDF 생성 완료", stage="assemble")

    return {"final_pdf_path": pdf_path or "", "final_word_path": ""}


# ═════════════════════════════════════════════════════════════════════════════
# Graph
# ═════════════════════════════════════════════════════════════════════════════

builder = StateGraph(AgentState)
builder.add_node("extract_pages", extract_pages_via_tool)
builder.add_node("classify_and_render", classify_and_render_via_tool)
builder.add_node("assemble_document", assemble_document_via_tool)

builder.set_entry_point("extract_pages")
builder.add_edge("extract_pages", "classify_and_render")
builder.add_edge("classify_and_render", "assemble_document")
builder.add_edge("assemble_document", END)

graph = builder.compile()


_progress_store: dict[str, dict] = {}


# 파이프라인 단계 식별자. 프런트엔드가 어느 노드를 실행 중인지 표시하는 데 씁니다.
#   extract   — 페이지에서 텍스트·영역 추출
#   classify  — 영역별 렌더 전략 판정
#   render    — 전략에 따라 수식·다이어그램·차트 생성
#   assemble  — PDF 조립
STAGES = ("extract", "classify", "render", "assemble")


def set_progress(
    conversion_id: str, percent: int, message: str = "", stage: str = ""
):
    """Update progress for a conversion job.

    stage 를 함께 넘기면 프런트엔드가 4단계 파이프라인 중 현재 위치를
    표시할 수 있습니다. 비워 두면 직전 단계를 유지합니다.
    """
    prev = _progress_store.get(conversion_id, {})
    _progress_store[conversion_id] = {
        "percent": percent,
        "message": message,
        "stage": stage or prev.get("stage", ""),
        # 단계별 세부 진행(예: 3/8 페이지)을 그대로 노출
        "detail": prev.get("detail", {}),
    }


def set_stage_detail(conversion_id: str, done: int, total: int):
    """현재 단계의 세부 진행 상황(완료/전체)을 기록합니다."""
    entry = _progress_store.setdefault(
        conversion_id, {"percent": 0, "message": "", "stage": "", "detail": {}}
    )
    entry["detail"] = {"done": done, "total": total}


def get_progress(conversion_id: str) -> dict:
    """Get current progress for a conversion job."""
    return _progress_store.get(
        conversion_id, {"percent": 0, "message": "", "stage": "", "detail": {}}
    )


def clear_progress(conversion_id: str):
    """Remove progress entry after completion."""
    _progress_store.pop(conversion_id, None)


def orchestrate_conversion_process(state: dict, conversion_id: str = "") -> dict:
    """Execute LangGraph StateGraph pipeline with progress tracking."""
    if conversion_id:
        set_progress(conversion_id, 0, "변환 준비 중...", stage="extract")

    state["_conversion_id"] = conversion_id
    result = graph.invoke(state)
    result.pop("_conversion_id", None)

    if conversion_id:
        set_progress(conversion_id, 100, "완료", stage="assemble")

    return result
