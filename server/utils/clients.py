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


@lru_cache(maxsize=4)
def get_langchain_openai(model: str = "gpt-4o"):
    """LangChain ChatOpenAI 인스턴스 (텍스트 생성용)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, api_key=os.getenv("OPENAI_API_KEY"))


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
