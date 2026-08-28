"""
assemble_pdf.py

Purpose:
- Assemble rendered page content into a single PDF file.

Design decisions:
- This tool merges text blocks and rendered image blocks in index order.
- HTML text is preserved and injected into the page template as .text-section content.
- Mathematical expressions are rendered in-browser with KaTeX at PDF generation time.
- Tall images are split into multiple chunks to reduce layout breakage and improve pagination.
- If Pillow is unavailable or image splitting fails, the original image is preserved.
- Local temporary image files are referenced with file:// paths and rendered through Puppeteer.

Supported output strategies:
- html_css
- preserve_original

Supported input content:
- html_text
- base64_png
"""

import os
import io
import time
import math
import base64
import logging
import tempfile
from langchain_core.tools import tool

from utils.puppeteer_runner import render_html_to_pdf

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# ------------------------------------------------------------------------------
# Prompt
# ------------------------------------------------------------------------------
_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
          onload="window.katexLoaded=true;"></script>
  <script>
    window.renderFinished = false;
    document.addEventListener("DOMContentLoaded", function() {
      var attempts = 0;
      var maxAttempts = 30;
      var checker = setInterval(function() {
        if (window.katexLoaded) {
          clearInterval(checker);
          document.querySelectorAll(".text-section").forEach(function(el) {
            el.innerHTML = el.innerHTML
              .replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, function(m, f) {
                try { return katex.renderToString(f.trim(), {displayMode:true, throwOnError:false}); }
                catch(e) { return m; }
              })
              .replace(/\\$(.+?)\\$/g, function(m, f) {
                try { return katex.renderToString(f.trim(), {displayMode:false, throwOnError:false}); }
                catch(e) { return m; }
              });
          });
          window.renderFinished = true;
        } else if (++attempts >= maxAttempts) {
          clearInterval(checker);
          window.renderFinished = true;
        }
      }, 80);
    });
  </script>
  <style>
    @page { size: A4; margin: 20mm 15mm; }

    body {
      font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
      font-size: 13px;
      line-height: 1.8;
      color: #222;
      margin: 0;
      padding: 0;
    }

    figure {
      text-align: center;
      margin: 16px 0;
      break-inside: auto;
      page-break-inside: auto;
    }

    figure img {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
      object-fit: contain;
    }

    .text-section { margin-bottom: 24px; }
    .text-section h1, .text-section h2, .text-section h3 {
      margin: 16px 0 8px;
      page-break-after: avoid;
    }
    .text-section ul, .text-section ol { padding-left: 24px; }
    .text-section table {
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0;
    }
    .text-section th, .text-section td {
      border: 1px solid #ccc;
      padding: 6px 10px;
    }
  </style>
</head>
<body>
{body}
</body>
</html>"""

# main.py 와 같은 환경변수를 본다. 한쪽만 볼륨을 가리키면 PDF 를 쓴 위치와
# 정적 서빙 위치가 어긋나 다운로드가 404 가 된다.
_CONVERTED_DIR = os.getenv("CONVERTED_DIR", "").strip() or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "converted")
)


def _split_tall_image_if_needed(image_b64: str, max_height_px: int = 1800) -> list[str]:
    if not _PIL_AVAILABLE:
        return [image_b64]

    try:
        img = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
        w, h = img.size

        if h <= max_height_px:
            return [image_b64]

        chunks = []
        count = math.ceil(h / max_height_px)

        for i in range(count):
            top = i * max_height_px
            bottom = min((i + 1) * max_height_px, h)
            cropped = img.crop((0, top, w, bottom))

            buf = io.BytesIO()
            cropped.save(buf, format="PNG", optimize=True)
            chunks.append(base64.b64encode(buf.getvalue()).decode())

        return chunks

    except Exception:
        return [image_b64]


def _save_temp_image(b64_data: str, name: str, tmp_dir: str) -> str:
    path = os.path.join(tmp_dir, f"{name}.png")
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    return path


@tool
def assemble_pdf(rendered_images: list[dict], output_path: str = "") -> str:
    """
    Assemble rendered page content into a PDF file.

    Args:
        rendered_images: List of rendered page items containing html_text or base64_png.
        output_path: Optional output PDF path.

    Returns:
        The final PDF file path.
    """
    sorted_items = sorted(rendered_images, key=lambda x: x.get("index", 0))

    with tempfile.TemporaryDirectory(prefix="pdf_assemble_") as tmp_dir:
        body_parts: list[str] = []
        img_count = 0
        text_count = 0

        for item in sorted_items:
            html_text = (item.get("html_text") or "").strip()
            base64_png = (item.get("base64_png") or "").strip()
            index = item.get("index", 0)

            if html_text:
                body_parts.append(f'<div class="text-section">{html_text}</div>')
                text_count += 1
                continue

            if base64_png:
                chunks = _split_tall_image_if_needed(base64_png)
                for chunk_idx, chunk_b64 in enumerate(chunks):
                    img_path = _save_temp_image(
                        chunk_b64,
                        f"img_{index}_{chunk_idx}",
                        tmp_dir,
                    )
                    body_parts.append(
                        f'<figure><img src="file://{img_path}" alt="image-{index}-{chunk_idx}"></figure>'
                    )
                    img_count += 1

        if not body_parts:
            raise ValueError("No content to assemble.")

        html = _PAGE_TEMPLATE.replace("{body}", "\n".join(body_parts))

        if not output_path:
            os.makedirs(_CONVERTED_DIR, exist_ok=True)
            output_path = os.path.join(
                _CONVERTED_DIR,
                f"output_{int(time.time())}.pdf",
            )

        result = render_html_to_pdf(
            html,
            output_path,
            timeout=60,
            extra_args=["--allow-file-access-from-files"],
        )

        logger.info(
            "[assemble_pdf] done path=%s text=%s images=%s",
            output_path, text_count, img_count
        )
        return result