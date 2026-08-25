"""
tool_render_illustration.py

Purpose:
- When the source image is NOT a photo but a structured visual
  (labeled schematic, structured figure, illustrated layout, etc.),
  analyze its structure via GPT-4o and regenerate a cleaner version
  via gpt-image-1.

Key design decisions:
1. No SVG text generation — that approach is unreliable for complex visuals.
2. Two-stage pipeline:
   - Step 1: GPT-4o analyzes the image structure in detail (text output).
   - Step 2: gpt-image-1 regenerates a cleaner image based on the analysis.
3. Anti-crop measures: explicit instructions to keep all elements visible.
4. Portrait / landscape detection for appropriate canvas size selection.
5. Falls back to preserve_original on any failure.

Notes:
- This tool does NOT assume the input is always a "diagram".
- It does NOT force an "educational" style.
- The input is treated as a non-photographic structured visual and
  processed accordingly.
"""

import logging
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from utils.clients import get_openai_client, get_langchain_openai, downscale_b64_image, image_content_part, log_usage

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Step 1: GPT-4o structure analysis prompt
# ------------------------------------------------------------------------------
# Key principles:
# - Do not assume the input is a "diagram" or "educational" material.
# - Extract labels, arrows, structure, layout, colors, relationships
#   in maximum detail.
# - Force the model to output "portrait" or "landscape" on the last line
#   so we can select the appropriate canvas size.
_ANALYSIS_PROMPT = """\
이 이미지의 모든 시각 구성 요소를 완벽하게 분석하고 기술하세요.
이 기술은 이미지 생성 AI에게 전달되어 원본을 재생성하는 데 직접 사용됩니다.
따라서 이 기술만으로 원본을 정확히 복원할 수 있을 정도로 상세해야 합니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 분석 항목 (반드시 모두 포함)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### A. 전체 요약
- 이 이미지가 무엇을 표현하는지 1-2줄로 설명
- 전체적인 시각 유형 (회로도, 힘의 다이어그램, 원자 구조, 개념도 등)

### B. 캔버스 구성
- 전체 레이아웃: 단일 도식 / 좌우 비교 / 상하 배열 / 격자 배치 등
- 각 영역의 상대적 크기와 위치 (예: "왼쪽 절반에 (가) 도식, 오른쪽 절반에 (나) 도식")
- 영역 사이에 구분선이나 라벨이 있으면 명시

### C. 도형 목록 (하나씩 모두 나열)
각 도형에 대해:
- 종류: 원, 타원, 사각형, 삼각형, 자유 곡선 등
- 크기: 큰/중간/작은, 다른 도형 대비 상대적 크기
- 위치: 캔버스 내 정확한 위치 (예: "중앙 상단", "좌측 하단 1/4 영역")
- 채움: 색상 채움 여부, 빗금, 점 패턴 등
- 테두리: 실선/점선/굵기

### D. 텍스트 라벨 목록 (하나씩 모두 나열)
각 라벨에 대해:
- **정확한 텍스트**: 원본 언어 그대로, 한 글자도 바꾸지 않고 기재
- **위치**: 어떤 도형/화살표 근처에 있는지
- **스타일**: 크기(크게/작게), 굵게, 기울임 여부

⚠ 한글 라벨 주의사항:
- 손글씨에서 비슷한 글자를 혼동하지 마세요
- "인력" ≠ "인덕", "척력" ≠ "흑력", "전기력" ≠ "정기력", "대전체" ≠ "대전채"
- 과학 용어는 문맥에 맞는 올바른 단어를 선택하세요
- 모든 라벨을 정확히 나열한 뒤, 마지막에 "라벨 목록: ..." 형태로 한번 더 정리하세요

### E. 화살표/연결선 목록 (하나씩 모두 나열)
각 화살표/선에 대해:
- 시작점 → 끝점 (어떤 도형에서 어떤 도형으로)
- 방향: 단방향(→) / 양방향(↔)
- 스타일: 직선/곡선, 실선/점선
- 의미: 힘의 방향, 흐름, 인과관계 등
- 화살표에 라벨이 붙어있으면 정확히 기재

### F. 기호
- +, -, 전하 기호, 수학 기호, 특수 문자의 정확한 위치와 의미
- 기호의 크기와 반복 횟수 (예: "표면에 + 기호 5개가 일렬로")

### G. 색상 정보
- 사용된 색상과 각각이 무엇을 의미하는지
- 색상이 구분에 중요한 역할을 하는 경우 반드시 명시

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 기술 품질 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ✅ 좋은 예: "중앙에 지름 약 3cm의 원이 있고, 원 내부 중앙에 '+' 기호가 있다. 원의 왼쪽에서 오른쪽을 향하는 빨간색 화살표가 있고, 화살표 위에 '인력'이라는 라벨이 있다."
- ❌ 나쁜 예: "원과 화살표가 있고 라벨이 붙어있다."
- 수량을 정확히: "몇 개" → "3개"
- 위치를 정확히: "옆에" → "오른쪽 위 대각선 방향으로 약 2cm 떨어진 곳에"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 마지막 줄 (정확히 한 단어만 출력)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
portrait — 세로가 더 긴 구성
landscape — 가로가 더 긴 구성
text_only — 텍스트/수식 위주이고 그림/도형이 거의 없는 경우
"""

# ------------------------------------------------------------------------------
# Step 2: gpt-image-1 regeneration prompt template
# ------------------------------------------------------------------------------
# Key principles:
# - Use neutral phrasing ("clean visual") without over-specifying the style.
# - Explicitly forbid converting the source into a different visual category.
# - Strongly enforce: no crop / full inclusion / margin / no information loss.
_REGEN_PROMPT_TEMPLATE = """\
아래 설명을 바탕으로 교육 자료에 들어갈 깔끔하고 전문적인 시각 자료를 생성하세요.
이것은 손글씨 원본을 디지털로 재구성하는 작업입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 1. 텍스트/라벨 규칙 ★★★ 최우선 ★★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 설명에 나온 모든 텍스트 라벨을 정확히 그대로 이미지에 포함하세요
- 한 글자도 바꾸지 마세요. 한 글자도 생략하지 마세요. 비슷한 글자로 대체하지 마세요.
- 한글 텍스트는 특히 주의하세요:
  ✗ "인력"을 "인덕"으로 바꾸면 안 됩니다
  ✗ "척력"을 "흑력"으로 바꾸면 안 됩니다
  ✗ "전기력"을 "정기력"으로 바꾸면 안 됩니다
  ✗ "대전체"를 "대전채"로 바꾸면 안 됩니다
- 텍스트는 충분히 크고 선명하게 렌더링하세요 (최소 14pt 느낌)
- 텍스트 배경과 글자 색상이 명확히 대비되어야 합니다 (흰 배경 + 검정 글자)
- +, -, 전하 기호, 화살표 방향 등 과학 기호를 정확하게 재현하세요
- 설명의 "라벨 목록"에 있는 텍스트를 생성 후 하나씩 대조하며 모두 포함되었는지 확인하세요

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 2. 구조/레이아웃
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 설명에 기술된 도형, 화살표, 연결선을 정확한 위치와 방향으로 배치하세요
- 여러 섹션(예: (가), (나))이 있으면 설명된 배치대로 모두 포함하세요
- 요소 간 크기 비율을 설명과 일치시키세요
- 원본의 시각적 유형을 임의로 변경하지 마세요 (회로도 → 플로차트 변환 금지)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 3. 시각 스타일
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 흰색 배경
- 깨끗하고 균일한 선 (2-3px 두께)
- 도형: 깔끔한 기하학적 형태, 명확한 윤곽선
- 화살표: 방향이 명확한 삼각형 화살촉
- 색상: 설명에 색상 정보가 있으면 따르고, 없으면 검정+파랑+빨강 기본 팔레트
- 전체적으로 교과서/참고서 품질의 깔끔한 도식

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 4. 캔버스/여백 (잘림 방지) ★★ 매우 중요 ★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 모든 도형, 화살표, 텍스트 라벨이 캔버스 안에 100% 보여야 합니다
- 이미지 경계에 잘리는 요소가 단 하나도 없어야 합니다
- 가장 바깥 요소에서 이미지 경계까지 최소 8%의 여백을 확보하세요
- 요소가 많아서 공간이 부족하면, 전체를 축소해서라도 모든 것을 포함하세요
- 특히 텍스트 라벨이 이미지 밖으로 벗어나지 않도록 주의하세요

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 5. 절대 금지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ 설명에 없는 요소를 임의로 추가
✗ 중요한 요소를 단순화하여 생략
✗ 텍스트 라벨을 임의로 수정하거나 번역
✗ 장식적 요소(그림자, 3D 효과, 그라데이션) 추가
✗ 이미지 경계에서 요소 잘림

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

설명:
{description}
"""


# ------------------------------------------------------------------------------
# Step 3: Cross-check verification prompt
# ------------------------------------------------------------------------------
_VERIFY_PROMPT = """\
첫 번째 이미지는 원본(손글씨), 두 번째 이미지는 AI가 재생성한 결과입니다.
재생성 결과가 원본을 충실히 재현했는지 엄격하게 검증하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 검증 절차 (순서대로 수행)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### STEP 1: 텍스트 라벨 전수 검사 [치명적 — 하나라도 틀리면 FAIL]
- 원본에 있는 모든 텍스트 라벨을 하나씩 나열하세요
- 각 라벨이 재생성에도 정확히 동일한 텍스트로 존재하는지 확인하세요
- 한글 글자 하나라도 다르면 FAIL (예: "인력"→"인덕", "전기력"→"정기력")
- 원본에 없는 텍스트가 재생성에 추가되었는지도 확인하세요

### STEP 2: 시각 요소 완전성 검사 [치명적]
- 원본의 모든 도형(원, 사각형, 삼각형 등)이 재생성에도 존재하는가?
- 모든 화살표가 올바른 방향과 연결로 존재하는가?
- +, -, 전하 기호 등 과학 기호가 올바른 위치에 있는가?
- 원본에 없는 불필요한 요소가 추가되지 않았는가?

### STEP 3: 구조/레이아웃 검사 [중요]
- 요소 간의 공간적 관계가 원본과 유사한가? (좌-우, 상-하 배치)
- 여러 섹션이 있는 경우 각각이 올바른 위치에 있는가?
- 요소 간 크기 비율이 원본과 유사한가?

### STEP 4: 잘림/가독성 검사 [치명적]
- 텍스트나 도형이 이미지 경계에서 잘려있지 않은가?
- 텍스트가 선명하고 읽을 수 있는가?
- 요소들이 겹쳐서 판독이 어려운 부분이 없는가?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 응답 형식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

첫 줄에 반드시: PASS 또는 FAIL

FAIL인 경우, 재생성 프롬프트에 직접 추가할 수 있는 구체적 수정 지시를 작성하세요:

오류 목록:
- [라벨오류] "원본텍스트" → "재생성텍스트" — 수정: "원본텍스트"로 정확히 표기할 것
- [누락] (구체적 요소) — 수정: (어디에 어떻게 추가할지)
- [잘림] (구체적 요소) — 수정: 전체를 축소하여 여백 확보할 것
- [추가요소] (불필요한 요소) — 수정: 해당 요소를 제거할 것
- [구조] (구체적 문제) — 수정: (올바른 배치 설명)

⚠ 판정 기준:
- 라벨 1개라도 글자가 다르면 → FAIL
- 중요 요소 1개라도 누락되면 → FAIL
- 잘림이 있으면 → FAIL
- 레이아웃이 약간 다른 정도는 → PASS (내용 정확성이 더 중요)
"""


def _detect_canvas_size(description: str) -> str:
    """
    Select gpt-image-1 canvas size based on portrait/landscape hint
    from the GPT-4o analysis output.

    Policy:
    - "portrait" in description -> 1024x1536
    - "landscape" or unclear    -> 1536x1024

    Rationale:
    - Square (1024x1024) tends to crop tall or wide visuals.
    - Splitting into portrait/landscape improves the chance of
      fitting all elements within the canvas.
    """
    text = (description or "").lower()
    if "portrait" in text:
        return "1024x1536"
    return "1536x1024"


@tool
def render_illustration(image_b64: str, index: int) -> dict:
    """
    Regenerate a structured visual as a cleaner image using GPT-4o analysis
    followed by gpt-image-1 generation.

    Args:
        image_b64: Base64-encoded PNG image.
        index: Source image index.

    Returns:
        On success:
            {"index": int, "strategy": "illustration_redraw", "base64_png": str}
        On fallback:
            {"index": int, "strategy": "preserve_original", "base64_png": str}
    """
    # --- Input validation ---
    # Empty base64 means generation is impossible; fall back immediately.
    if not image_b64:
        logger.error("[render_illustration] index=%s: empty image_b64", index)
        return {
            "index": index,
            "strategy": "preserve_original",
            "base64_png": "",
        }

    # --- Step 1: GPT-4o structure analysis ---
    # Role:
    # - Convert the source visual into a detailed text description.
    # - Cover labels, shapes, positions, relationships, layout.
    # - Provide a portrait/landscape hint on the last line.
    try:
        llm = get_langchain_openai(task="vision")

        analysis_content = [
            {"type": "text", "text": _ANALYSIS_PROMPT},
            image_content_part(image_b64, detail="high"),
        ]

        analysis_response = llm.invoke([HumanMessage(content=analysis_content)])
        log_usage("illustration.analysis", analysis_response)
        description = (analysis_response.content or "").strip()

        # If the description is too short, treat it as analysis failure.
        # Regenerating from a shallow description risks hallucination.
        if len(description) < 50:
            logger.warning(
                "[render_illustration] index=%s: analysis too short -> fallback",
                index,
            )
            return {
                "index": index,
                "strategy": "preserve_original",
                "base64_png": image_b64,
            }

        # Check if analysis determined this is text-only (not a visual)
        last_line = description.strip().split("\n")[-1].strip().lower()
        if "text_only" in last_line:
            logger.info("[render_illustration] index=%s: text_only detected -> skip", index)
            return {
                "index": index,
                "strategy": "text_only",
                "base64_png": "",
            }

        # Select canvas aspect ratio from the analysis output.
        size = _detect_canvas_size(description)

        logger.info(
            "[render_illustration] index=%s: analysis complete (length=%s, size=%s)",
            index,
            len(description),
            size,
        )

    except Exception as e:
        # If analysis fails, preserving the original is the safest option.
        logger.error(
            "[render_illustration] index=%s: analysis failed (%s: %s) -> fallback",
            index,
            type(e).__name__,
            e,
        )
        return {
            "index": index,
            "strategy": "preserve_original",
            "base64_png": image_b64,
        }

    # --- Step 2 & 3: gpt-image-1 regeneration + cross-check verification ---
    # Up to 2 attempts: generate, verify, retry once if FAIL.
    try:
        client = get_openai_client()
        best_b64 = None
        verify_feedback = ""
        max_attempts = 2

        for attempt in range(max_attempts):
            # --- Generate ---
            regen_prompt = _REGEN_PROMPT_TEMPLATE.format(description=description)
            if attempt > 0 and verify_feedback:
                # Append verification feedback for retry
                regen_prompt += f"\n\n이전 생성에서 발견된 오류 (반드시 수정하세요):\n{verify_feedback}"

            result = client.images.generate(
                model="gpt-image-1",
                prompt=regen_prompt,
                size=size,
                quality="high",
            )

            output_b64 = result.data[0].b64_json
            if not output_b64:
                raise ValueError("Image generation API returned empty output.")

            best_b64 = output_b64

            # --- Cross-check verification ---
            try:
                verify_content = [
                    {"type": "text", "text": _VERIFY_PROMPT},
                    image_content_part(image_b64, detail="high"),
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{output_b64}"},
                    },
                ]
                verify_response = llm.invoke([HumanMessage(content=verify_content)])
                log_usage("illustration.verify", verify_response)
                verify_text = (verify_response.content or "").strip()
                first_line = verify_text.split("\n")[0].strip().upper()

                if "PASS" in first_line:
                    logger.info(
                        "[render_illustration] index=%s: verification PASS (attempt %s)",
                        index, attempt + 1,
                    )
                    break  # Good enough
                else:
                    verify_feedback = verify_text.split("\n", 1)[1].strip() if "\n" in verify_text else verify_text
                    logger.warning(
                        "[render_illustration] index=%s: verification FAIL (attempt %s): %s",
                        index, attempt + 1, verify_feedback[:200],
                    )
                    # Continue to next attempt (or exit loop if max_attempts reached)

            except Exception as ve:
                logger.warning(
                    "[render_illustration] index=%s: verification error (%s) — using current result",
                    index, ve,
                )
                break  # Verification failed technically; use current result

        logger.info(
            "[render_illustration] index=%s: regeneration success (size=%s)",
            index, size,
        )

        return {
            "index": index,
            "strategy": "illustration_redraw",
            "base64_png": best_b64,
        }

    except Exception as e:
        # If regeneration fails, keeping the original is better than nothing.
        logger.error(
            "[render_illustration] index=%s: regeneration failed (%s: %s) -> fallback",
            index,
            type(e).__name__,
            e,
        )
        return {
            "index": index,
            "strategy": "preserve_original",
            "base64_png": image_b64,
        }