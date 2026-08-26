"""
utils/clients — LLM·Genai 클라이언트 싱글턴 + 공용 JSON 파서.

모든 tool 모듈이 이 모듈을 통해 클라이언트에 접근한다.
매 호출마다 인스턴스를 재생성하지 않으므로 커넥션 풀이 재사용된다.
"""

import os
import re
import json
import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


# ─── Client Singletons ────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_openai_client():
    """OpenAI Python SDK 클라이언트 (이미지 생성용)."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


# ─── 작업별 모델·파라미터 ──────────────────────────────────────────────────────
#
# 이전에는 모든 작업이 gpt-4o 를 기본값 파라미터 없이 호출했다. 두 가지 문제가
# 있었다.
#
#   1) 분류처럼 "5개 중 하나 고르기" 작업에도 최상위 모델을 썼다.
#      영역 수만큼 호출되므로 비용이 그대로 곱해진다.
#   2) max_tokens·temperature 가 없어 출력 길이에 상한이 없고,
#      기본 temperature(1.0) 때문에 같은 입력에도 결과가 흔들렸다.
#
# 작업 성격에 맞춰 아래 프로필로 나눈다. 환경변수로 덮어쓸 수 있게 해서
# 모델을 올리고 내리는 실험을 코드 수정 없이 할 수 있도록 했다.
#
#   classify — 판정만 하면 되므로 가볍고 확정적인 설정
#   generate — 코드·수식을 만들어야 하므로 추론 품질이 필요
#   vision   — 이미지에서 구조를 읽어내는 작업

_TASK_PROFILES = {
    "classify": {
        "env": "MODEL_CLASSIFY",
        # 5개 라벨 중 하나를 고르는 작업이라 상위 모델이 필요 없다.
        # 영역 수만큼 호출되므로 여기가 비용에 가장 민감하다.
        "default": "gpt-4o-mini",
        "temperature": 0.0,   # 같은 영역은 항상 같은 전략으로 판정되어야 한다
        "max_tokens": 400,    # JSON 판정 결과만 나오면 된다
    },
    "generate": {
        "env": "MODEL_GENERATE",
        # 코드·수식을 만들어야 하므로 품질 우선. 더 상위 모델을 쓰려면
        # MODEL_GENERATE 로 지정한다(예: gpt-4.1, gpt-5 등).
        "default": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 4000,   # mermaid/chartjs/latex 코드 블록
    },
    "vision": {
        "env": "MODEL_VISION",
        # 이미지에서 구조를 읽어내는 작업. MODEL_VISION 으로 상향 가능.
        "default": "gpt-4o",
        "temperature": 0.1,
        "max_tokens": 4000,
    },
}


@lru_cache(maxsize=8)
def get_langchain_openai(model: str = "gpt-4o", task: str = ""):
    """LangChain ChatOpenAI 인스턴스.

    task 를 주면 해당 프로필의 모델·temperature·max_tokens 가 적용된다.
    task 없이 부르면 이전과 동일하게 동작한다(호환용).
    """
    from langchain_openai import ChatOpenAI

    kwargs: dict = {"api_key": os.getenv("OPENAI_API_KEY")}

    profile = _TASK_PROFILES.get(task)
    if profile:
        kwargs["model"] = os.getenv(profile["env"], "").strip() or profile["default"]
        kwargs["temperature"] = profile["temperature"]
        kwargs["max_tokens"] = profile["max_tokens"]
    else:
        kwargs["model"] = model

    return ChatOpenAI(**kwargs)


def log_usage(tag: str, response) -> None:
    """LLM 응답의 토큰 사용량을 로그로 남긴다.

    최적화 효과를 눈으로 확인하려면 실제 사용량이 필요한데, 이전에는
    어디에서도 기록하지 않아 추정만 가능했다.
    """
    try:
        meta = getattr(response, "usage_metadata", None) or {}
        if not meta:
            return
        logger.info(
            "[usage] %s input=%s output=%s total=%s",
            tag,
            meta.get("input_tokens"),
            meta.get("output_tokens"),
            meta.get("total_tokens"),
        )
    except Exception:  # noqa: BLE001
        pass


@lru_cache(maxsize=1)
def get_genai_client():
    """Google Generative AI 클라이언트."""
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


# ─── JSON Parsing Utility ─────────────────────────────────────────────────────


def parse_llm_json(text: str) -> Any:
    """
    LLM 응답에서 JSON을 안전하게 추출한다.

    파싱 전략 (우선순위):
      1. ```json ... ``` 코드 펜스 블록
      2. bracket-counting 으로 최외곽 { } 또는 [ ] 추출
      3. 전체 텍스트를 json.loads 시도

    Returns:
        파싱된 dict/list. 실패 시 빈 dict 반환.
    """
    if not text or not text.strip():
        return {}

    # Strategy 1: code fence
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 2: bracket counting (handles nested braces in SVG, CSS, etc.)
    for open_ch, close_ch in [('{', '}'), ('[', ']')]:
        start = text.find(open_ch)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == open_ch:
                depth += 1
            elif text[i] == close_ch:
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    break

    # Strategy 3: raw parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.warning("parse_llm_json: 모든 파싱 전략 실패")
        return {}


# ─── 이미지 입력 최적화 ────────────────────────────────────────────────────────

# 비전 모델에 보낼 이미지의 긴 변 상한(px).
#
# ⚠️ 이 값은 토큰을 줄이지 않는다. 실측 결과 4032px / 2048px / 1536px /
#    768px 모두 입력 토큰이 822 로 동일했다. 비전 토큰은 서버 측에서
#    정해진 타일 규격으로 환산되므로 그 규격을 넘는 해상도를 보내도
#    토큰은 늘지 않는다.
#
# 축소의 효과는 전송량과 지연 시간이다. 6MB -> 0.9MB 로 줄면서 응답이
# 4.0초 -> 1.5초가 되었다. 그래서 유지한다.
#
# 토큰을 줄이려면 detail 파라미터를 쓴다(아래 image_content_part 참고).
# 같은 모델에서 detail="low" 만으로 822 -> 142 (82.7% 감소)였다.
#
# 손글씨 판독에는 1536px 이면 충분하다. 더 낮추면 인식률만 떨어지고
# 비용은 그대로이므로 무리해서 내릴 이유가 없다.
_MAX_IMAGE_SIDE = int(os.getenv("MAX_IMAGE_SIDE", "1536"))


def downscale_b64_image(image_b64: str, max_side: int | None = None) -> str:
    """base64 PNG 의 긴 변을 max_side 이하로 줄인다.

    이미 작으면 원본을 그대로 돌려준다. 어떤 이유로든 실패하면 원본을
    반환하므로, 이 함수 때문에 파이프라인이 멈추지는 않는다.
    """
    if not image_b64:
        return image_b64

    limit = max_side or _MAX_IMAGE_SIDE
    try:
        import base64 as _b64
        import io as _io
        from PIL import Image

        raw = _b64.b64decode(image_b64)
        img = Image.open(_io.BytesIO(raw))
        w, h = img.size
        longest = max(w, h)
        if longest <= limit:
            return image_b64

        ratio = limit / float(longest)
        img = img.convert("RGB").resize(
            (max(1, int(w * ratio)), max(1, int(h * ratio))), Image.LANCZOS
        )
        buf = _io.BytesIO()
        # 손글씨는 선 대비가 중요하므로 PNG 를 유지한다.
        img.save(buf, format="PNG", optimize=True)
        out = _b64.b64encode(buf.getvalue()).decode()

        logger.info(
            "[image] downscaled %sx%s -> %sx%s (%.0fKB -> %.0fKB)",
            w, h, img.width, img.height, len(raw) / 1024, len(buf.getvalue()) / 1024,
        )
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("[image] downscale 실패, 원본 사용: %s", exc)
        return image_b64


def image_content_part(image_b64: str, detail: str = "high") -> dict:
    """비전 입력용 image_url 파트를 만든다.

    축소를 여기서 함께 처리한다. 호출부마다 downscale 을 부르게 하면
    빠뜨리는 곳이 생기므로, 이미지가 모델로 나가는 유일한 통로에서 보장한다.

    detail 을 명시하지 않으면 고해상도 모드로 처리된다. 구조만 파악하면
    되는 작업(분류 등)은 "low" 로 충분하다.

    실측(gpt-4o, 동일 이미지): high=822 토큰, low=142 토큰 (82.7% 감소).
    토큰 절감은 해상도가 아니라 이 파라미터에서 나온다.
    """
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/png;base64,{downscale_b64_image(image_b64)}",
            "detail": detail,
        },
    }
