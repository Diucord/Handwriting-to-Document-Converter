"""
tool_render_math.py

Pipeline:
  Step 1: GPT-4o analyzes the math graph image and generates matplotlib code.
  Step 2: Execute the matplotlib code in a restricted sandbox to produce PNG.

Suitable inputs:
- Function graphs (parabolas, polynomials, trigonometric, etc.)
- Coordinate-based plots with axes labels (alpha, beta, etc.)
- Shaded area between curves
- Graphs with labeled points, tangent lines, intersections

NOT suitable for:
- Conceptual diagrams, flowcharts, schematics
- Circuit diagrams, atomic structures
- Non-mathematical illustrations

Falls back to preserve_original on any failure.
"""

import io
import base64
import logging
import tempfile
import os
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from utils.clients import get_langchain_openai, parse_llm_json, downscale_b64_image, image_content_part, log_usage

logger = logging.getLogger(__name__)

# ── Step 1: GPT-4o analysis → matplotlib code ─────────────────────────────────

# ------------------------------------------------------------------------------
# Prompt
# ------------------------------------------------------------------------------
_ANALYSIS_PROMPT = """\
이 손글씨 수학 그래프를 분석하고 matplotlib 코드로 정확히 재현하세요.
```json 블록 안에 "code" 키 하나만 있는 JSON 객체를 반환하세요.

━━━ 코드 환경 ━━━
- import: matplotlib, numpy만 사용 가능
- 저장: plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor='white')
  - OUTPUT_PATH 변수는 이미 정의되어 있음
- plt.show() 호출 금지
- 저장 후 plt.close() 호출 필수

━━━ 그래프 재현 규칙 ━━━

1. **함수 정확성** (최우선)
   - 곡선의 수학적 형태를 정확히 파악하세요 (포물선, 3차, 삼각, 지수, 로그 등)
   - 원본에서 꼭짓점, 교점, 영점(x절편, y절편)이 보이면 정확한 계수를 역추정
   - 예: 꼭짓점이 (2, -1)인 포물선 → y = (x-2)² - 1

2. **특수 요소 재현**
   - 색칠 영역: plt.fill_between() + alpha=0.3, 원본 범위 정확히
   - 교점: plt.plot()으로 점 표시 + 좌표 텍스트 annotate
   - 접선/점근선: 점선(linestyle='--')으로 표시
   - 축 위 특수점 (α, β, γ 등): 유니코드 그리스 문자 사용

3. **라벨 완전성**
   - 이미지에 있는 모든 텍스트 라벨을 빠짐없이 포함
   - 원본 언어 그대로 유지 (한글 포함)
   - 함수식 라벨: LaTeX 형식 사용 (r'$f(x) = x^2$')

━━━ 스타일 규칙 ━━━

```python
# 좌표계 설정 (원점 중심 수학 스타일)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_position('zero')
ax.spines['left'].set_position('zero')

# 축 화살표
ax.plot(1, 0, '>k', transform=ax.get_yaxis_transform(), clip_on=False)
ax.plot(0, 1, '^k', transform=ax.get_xaxis_transform(), clip_on=False)

# 격자
ax.grid(True, linestyle='--', alpha=0.3, color='gray')

# 색상: 주요=파랑('#2563eb'), 보조=빨강('#dc2626'), 3차=초록('#16a34a')
# 선 굵기: linewidth=2
# 라벨 크기: fontsize=13
```

━━━ 축 범위 ━━━
- 모든 중요 요소(교점, 꼭짓점, 라벨)가 여유 있게 보이도록 설정
- 원본보다 약간 넓게 설정하여 잘림 방지

━━━ 출력 형식 ━━━
```json
{
  "code": "import matplotlib.pyplot as plt\\nimport numpy as np\\n..."
}
```
"""

# ── Step 2: Execute matplotlib code ───────────────────────────────────────────


def _execute_matplotlib_code(code: str) -> str:
    """
    Execute matplotlib code in a controlled environment.
    Returns base64-encoded PNG or empty string on failure.
    """
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Provide OUTPUT_PATH to the code
        exec_globals = {"OUTPUT_PATH": tmp_path}
        exec(code, exec_globals)

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise ValueError("matplotlib code did not produce output file")

        with open(tmp_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@tool
def render_math(image_b64: str, index: int) -> dict:
    """
    Recreate a math graph using GPT-4o analysis + matplotlib code generation.

    Args:
        image_b64: Base64-encoded PNG image of a math graph.
        index: Source image index.

    Returns:
        On success:
            {"index": int, "strategy": "math_graph", "base64_png": str}
        On fallback:
            {"index": int, "strategy": "preserve_original", "base64_png": str}
    """
    if not image_b64:
        logger.error("[render_math] index=%s: empty image_b64", index)
        return {"index": index, "strategy": "preserve_original", "base64_png": ""}

    # ── Step 1: GPT-4o → matplotlib code ──
    try:
        llm = get_langchain_openai(task="generate")
        response = llm.invoke([HumanMessage(content=[
            {"type": "text", "text": _ANALYSIS_PROMPT},
            image_content_part(image_b64, detail="high"),
        ])])
        log_usage("math", response)

        parsed = parse_llm_json(response.content or "")
        if not isinstance(parsed, dict):
            raise ValueError(f"LLM output is not a dict: {type(parsed)}")

        code = (parsed.get("code") or "").strip()
        if not code or "matplotlib" not in code:
            raise ValueError("LLM did not produce valid matplotlib code")

        logger.info("[render_math] index=%s: code generated (len=%s)", index, len(code))

    except Exception as e:
        logger.error("[render_math] index=%s: code generation failed (%s) -> fallback", index, e)
        return {"index": index, "strategy": "preserve_original", "base64_png": image_b64}

    # ── Step 2: Execute matplotlib code ──
    try:
        output_b64 = _execute_matplotlib_code(code)
        if not output_b64:
            raise ValueError("matplotlib execution produced empty output")

        logger.info("[render_math] index=%s: render success", index)
        return {"index": index, "strategy": "math_graph", "base64_png": output_b64}

    except Exception as e:
        logger.error("[render_math] index=%s: execution failed (%s) -> fallback", index, e)
        return {"index": index, "strategy": "preserve_original", "base64_png": image_b64}
