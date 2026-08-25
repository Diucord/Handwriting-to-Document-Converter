"""
tool_render_mermaid.py

Purpose:
- Convert simple node-link structure visuals into Mermaid code,
  then render to PNG via HTML + Mermaid CDN + Puppeteer.

Suitable inputs:
- Simple flowcharts
- Box + arrow structures
- Process diagrams
- State transition diagrams
- Simple concept relationship maps

NOT suitable for:
- Layout-sensitive or precision-dependent visuals
- Complex illustrations or schematics
- Circuit diagrams
- Atomic structure diagrams
- Charge/force direction visuals
- Coordinate/geometry-based drawings
- Complex compound structures that Mermaid cannot represent

Policy:
- Only use Mermaid when it can faithfully represent the structure.
- When in doubt, fall back to preserve_original.
"""

import logging
from html import escape as html_escape
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from utils.clients import get_langchain_openai, parse_llm_json
from utils.puppeteer_runner import render_html_to_png

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Prompt
# ------------------------------------------------------------------------------
_MERMAID_PROMPT = """\
이 이미지를 분석하고 Mermaid 다이어그램으로 변환하세요.

━━━ 적합성 판단 ━━━

✅ 변환 적합:
- 3~10개 노드의 단순 플로차트 (시작→처리→끝)
- 순서가 있는 프로세스 다이어그램
- 상태 전이도 (A→B→C)
- 박스+화살표의 명확한 관계도

❌ 변환 부적합 (is_suitable: false 반환):
- 자유 배치 일러스트, 과학 도식, 회로도
- 좌표/기하학 기반 도형
- 10개 이상 노드 또는 복잡한 교차 연결
- 레이아웃 자체가 의미를 가지는 다이어그램
- Mermaid 문법으로 표현 불가능한 구조

━━━ 출력 형식 ━━━

적합한 경우:
```json
{
  "is_suitable": true,
  "title": "다이어그램 제목",
  "mermaid_code": "graph TD\\n  A[시작] --> B[처리]\\n  B --> C[끝]"
}
```

부적합한 경우:
```json
{
  "is_suitable": false,
  "title": "",
  "mermaid_code": ""
}
```

━━━ Mermaid 코드 작성 규칙 ━━━
1. 노드 ID는 영문 (A, B, C...), 라벨만 한글 → A[한글 라벨]
2. 원본의 모든 노드와 연결을 빠짐없이 포함
3. 화살표 방향을 원본과 정확히 일치시키세요
4. 원본 라벨 텍스트를 한 글자도 바꾸지 마세요
5. 유효한 Mermaid 문법만 사용 (특수문자는 따옴표로 감싸기)
6. 기본은 graph TD (위→아래), 가로 흐름이면 graph LR
7. 라벨에 괄호()나 특수문자가 있으면 ["라벨"] 형식 사용
"""

# ------------------------------------------------------------------------------
# HTML template
# ------------------------------------------------------------------------------
_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      margin: 20px;
      font-family: sans-serif;
      color: #222;
    }}
    h3 {{
      margin: 0 0 12px;
      font-size: 18px;
      font-weight: 600;
    }}
    .wrap {{
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }}
    .mermaid {{
      max-width: 100%;
    }}
  </style>
</head>
<body>
  {title_html}
  <div class="wrap">
    <div class="mermaid">
{mermaid_code}
    </div>
  </div>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose'
    }});
    // Allow enough time for Mermaid rendering before signaling completion.
    setTimeout(function() {{
      window.renderFinished = true;
    }}, 1200);
  </script>
</body>
</html>
"""


def _build_title_html(title: str) -> str:
    """Wrap title string in an h3 tag. Return empty string if title is empty."""
    title = (title or "").strip()
    if not title:
        return ""
    return f"<h3>{html_escape(title)}</h3>"


@tool
def render_mermaid(image_b64: str, index: int) -> dict:
    """
    Convert a simple node-link visual into Mermaid code and render it as PNG.

    Args:
        image_b64: Base64-encoded PNG image.
        index: Source image index.

    Returns:
        On success:
            {"index": int, "strategy": "mermaid", "base64_png": str}
        On fallback:
            {"index": int, "strategy": "preserve_original", "base64_png": str}
    """
    # --- Input validation ---
    if not image_b64:
        logger.error("[render_mermaid] index=%s: empty image_b64", index)
        return {
            "index": index,
            "strategy": "preserve_original",
            "base64_png": "",
        }

    llm = get_langchain_openai("gpt-4o")

    content = [
        {"type": "text", "text": _MERMAID_PROMPT},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
        },
    ]

    try:
        # --- Step 1: LLM -> Mermaid JSON ---
        response = llm.invoke([HumanMessage(content=content)])
        parsed = parse_llm_json(response.content or "")

        if not isinstance(parsed, dict):
            raise ValueError(f"LLM response is not a dict: {type(parsed)}")

        is_suitable = bool(parsed.get("is_suitable", False))
        title = (parsed.get("title") or "").strip()
        mermaid_code = (parsed.get("mermaid_code") or "").strip()

        # If Mermaid is not suitable, fall back immediately.
        if not is_suitable:
            logger.info(
                "[render_mermaid] index=%s: not suitable for Mermaid -> fallback",
                index,
            )
            return {
                "index": index,
                "strategy": "preserve_original",
                "base64_png": image_b64,
            }

        # Empty Mermaid code is treated as failure.
        if not mermaid_code:
            raise ValueError("Mermaid conversion marked suitable, but mermaid_code is empty")

        # --- Step 2: Build HTML ---
        html = _HTML_TEMPLATE.format(
            title_html=_build_title_html(title),
            mermaid_code=mermaid_code,
        )

        # --- Step 3: Puppeteer rendering ---
        # Mermaid needs JS initialization time, so use a generous timeout.
        png_b64 = render_html_to_png(html, timeout=45)

        if not png_b64:
            raise ValueError("render_html_to_png returned empty output")

        logger.info("[render_mermaid] index=%s: render success", index)
        return {
            "index": index,
            "strategy": "mermaid",
            "base64_png": png_b64,
        }

    except Exception as e:
        # Conservative failure handling for Mermaid conversion.
        # Keeping the original is better than a broken Mermaid diagram.
        logger.error(
            "[render_mermaid] index=%s: failed (%s: %s) -> fallback",
            index,
            type(e).__name__,
            e,
        )
        return {
            "index": index,
            "strategy": "preserve_original",
            "base64_png": image_b64,
        }