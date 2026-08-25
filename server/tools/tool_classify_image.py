"""
tool_classify_image.py

Purpose:
- Classify a single visual placeholder region and decide how it should be rendered.

Design decisions:
- This tool operates on extracted visual regions, not full text pages.
- The classifier remains reconstruction-first when a specialized renderer is structurally compatible.
- preserve_original remains a valid strategy for ambiguous, text-sensitive, or unsupported regions.
- Strategy normalization should correct malformed labels, but must not rewrite preserve_original into redraw.

Supported output strategies:
- math_graph
- mermaid
- chartjs
- illustration_redraw
- preserve_original
"""

import logging
from typing import Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from utils.clients import get_langchain_openai, parse_llm_json, downscale_b64_image, image_content_part, log_usage

logger = logging.getLogger(__name__)

_CLASSIFY_PROMPT = """\
이 이미지를 분석하고, 최적의 렌더링 전략을 결정하세요.
추가 텍스트 없이 정확히 하나의 JSON 객체만 반환하세요.

이 이미지는 문서 페이지에서 크롭된 시각적 영역입니다.
이 영역은 이미 "시각 요소가 있는 영역"으로 판단되어 크롭된 것이므로,
대부분의 경우 재생성(illustration_redraw)이 기본 선택입니다.

━━━ 출력 형식 ━━━

```json
{
  "primary_type": "math_graph" | "diagram" | "chart" | "structured_visual" | "scientific_visual" | "formula_card" | "other",
  "render_strategy": "math_graph" | "mermaid" | "chartjs" | "illustration_redraw" | "preserve_original" | "text_only",
  "reason": "한 줄 근거 설명",
  "confidence": "high" | "medium" | "low"
}
```

━━━ 전략 선택 가이드 ━━━

★ 기본값: "illustration_redraw" ★
도형, 화살표, 라벨, 기호 등 시각적 요소가 하나라도 있으면 illustration_redraw를 선택하세요.
이것이 가장 안전하고 범용적인 전략입니다.

특수 전략 (해당 렌더러가 명확히 더 적합한 경우만):

● "math_graph" — 좌표축 + 수학 함수 곡선이 있는 그래프
  → x/y 축 위에 포물선, 삼각함수, 다항함수 등의 곡선이 그려진 경우만
  ✗ 부적합: 축만 있는 다이어그램, 수학 공식 카드, 기하학 도형

● "chartjs" — 정형 데이터 차트
  → 막대 그래프, 선 그래프, 원형 차트 등 수치 데이터 시각화
  ✗ 부적합: 비정형 다이어그램, 개념도

● "mermaid" — 단순 노드-링크 구조 (3~10개 노드)
  → 단순한 플로차트, 프로세스 다이어그램, 상태 전이도
  ✗ 부적합: 자유형 배치, 회로도, 밀집 라벨

예외 전략 (매우 드문 경우만):

● "text_only" — 도형/그림이 전혀 없고 100% 텍스트/수식만 있는 경우
  ⚠ 주의: 텍스트 라벨이 붙은 다이어그램은 text_only가 아닙니다!
  ⚠ 화살표, 원, 사각형, 선이 하나라도 있으면 text_only가 아닙니다!
  → 순수 손글씨 텍스트만 있는 극히 예외적인 경우에만 선택

● "preserve_original" — 재생성이 구조적으로 불가능한 경우만 (최후의 수단)
  → 실제 사진, 극도로 복잡한 영역
  ⚠ 이 전략은 거의 사용하지 마세요.

━━━ 핵심 원칙 ━━━
1. 이 영역은 이미 시각 요소로 판단되어 여기 온 것입니다 → illustration_redraw가 기본값
2. 도형/화살표/기호가 하나라도 보이면 → illustration_redraw (text_only 아님!)
3. 특수 렌더러(math_graph, chartjs, mermaid)는 확실한 경우만 선택
4. 애매하면 무조건 illustration_redraw
5. text_only와 preserve_original은 극히 예외적인 경우만
"""

_ALLOWED_STRATEGIES = {
    "math_graph",
    "mermaid",
    "chartjs",
    "illustration_redraw",
    "preserve_original",
    "text_only",
}


def _coerce_text(value: Any, default: str = "") -> str:
    return str(value or default).strip()


def _normalize_strategy(strategy: str, confidence: str, primary_type: str) -> str:
    strategy = _coerce_text(strategy, "illustration_redraw")
    confidence = _coerce_text(confidence, "low").lower()
    primary_type = _coerce_text(primary_type, "other").lower()

    aliases = {
        "illustration": "illustration_redraw",
        "diagram": "illustration_redraw",
        "flowchart": "mermaid",
        "graph": "math_graph",
        "chart": "chartjs",
        "preserve": "illustration_redraw",
    }
    strategy = aliases.get(strategy, strategy)

    if strategy not in _ALLOWED_STRATEGIES:
        if primary_type == "chart":
            return "chartjs"
        if primary_type == "math_graph":
            return "math_graph"
        # 기본값: illustration_redraw (preserve_original 아님)
        return "illustration_redraw"

    # preserve_original은 극히 드문 경우만 허용
    # confidence가 high가 아닌데 preserve_original이면 → illustration_redraw로 전환
    if strategy == "preserve_original" and confidence != "high":
        return "illustration_redraw"

    return strategy


def _normalize_result(parsed: dict, page_index: int, placeholder_index: int, image_b64: str) -> dict:
    strategy = _normalize_strategy(
        parsed.get("render_strategy"),
        parsed.get("confidence"),
        parsed.get("primary_type"),
    )
    confidence = _coerce_text(parsed.get("confidence"), "low").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    primary_type = _coerce_text(parsed.get("primary_type"), "other")
    reason = _coerce_text(parsed.get("reason"), "")
    region_id = f"{page_index}:{placeholder_index}"

    return {
        "page_index": page_index,
        "placeholder_index": placeholder_index,
        "region_id": region_id,
        "primary_type": primary_type,
        "render_strategy": strategy,
        "reason": reason,
        "confidence": confidence,
        "original_b64": image_b64,
    }


@tool
def classify_image(image_b64: str, page_index: int, placeholder_index: int) -> dict:
    """Classify a single visual placeholder region and decide the rendering strategy."""
    region_id = f"{page_index}:{placeholder_index}"

    if not image_b64:
        logger.warning("[classify_image] region=%s: empty image_b64 -> preserve_original", region_id)
        return {
            "page_index": page_index,
            "placeholder_index": placeholder_index,
            "region_id": region_id,
            "primary_type": "other",
            "render_strategy": "preserve_original",
            "reason": "empty image input",
            "confidence": "low",
            "original_b64": image_b64,
        }

    llm = get_langchain_openai(task="classify")
    content = [
        {"type": "text", "text": _CLASSIFY_PROMPT},
        image_content_part(image_b64, detail="low"),
    ]

    try:
        response = llm.invoke([HumanMessage(content=content)])
        log_usage("classify", response)
        raw_content = response.content
        if isinstance(raw_content, list):
            text = "\n".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in raw_content)
        else:
            text = str(raw_content or "")
        parsed = parse_llm_json(text)
        if not isinstance(parsed, dict):
            raise ValueError(f"LLM output is not a dict: {type(parsed)}")

        result = _normalize_result(parsed, page_index, placeholder_index, image_b64)
        logger.info(
            "[classify_image] region=%s strategy=%s confidence=%s primary=%s reason=%s",
            region_id,
            result["render_strategy"],
            result["confidence"],
            result["primary_type"],
            result["reason"],
        )
        return result

    except Exception as e:
        logger.warning(
            "[classify_image] region=%s stage=classification_failed error=%s:%s -> illustration_redraw",
            region_id,
            type(e).__name__,
            e,
        )
        return {
            "page_index": page_index,
            "placeholder_index": placeholder_index,
            "region_id": region_id,
            "primary_type": "other",
            "render_strategy": "illustration_redraw",
            "reason": f"classification failed: {type(e).__name__}",
            "confidence": "low",
            "original_b64": image_b64,
        }