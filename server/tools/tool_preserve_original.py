"""
tool_preserve_original.py

Purpose:
- Preserve the original region image while applying only light cleanup.

Design decisions:
- This tool is the terminal fallback for renderer failure and structurally unsupported regions.
- It is valid within a reconstruction-first pipeline when redraw would likely damage fidelity.
- Refinement remains intentionally conservative to avoid altering source meaning.

Supported output strategies:
- preserve_original
"""

import base64
import io
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def _refine(image_b64: str) -> str:
    if not _PIL_AVAILABLE:
        return image_b64
    try:
        img = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
        img = ImageOps.autocontrast(img, cutoff=2)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageEnhance.Sharpness(img).enhance(1.8)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return image_b64


@tool
def preserve_original(image_b64: str, index: int, region_id: str = "") -> dict:
    """Preserve the original image and apply only light cleanup."""
    target = region_id or str(index)
    logger.info("[preserve_original] region=%s stage=preserve", target)
    return {"index": index, "strategy": "preserve_original", "base64_png": _refine(image_b64)}