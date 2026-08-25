"""
tool_render_chartjs — Convert graph/chart images to Chart.js JSON and render to PNG via Puppeteer.

Flow:
  1. GPT-4o: analyze image → generate Chart.js config JSON
  2. Insert Chart.js CDN + canvas into HTML template
  3. puppeteer_runner.render_html_to_png() → base64 PNG

Changes (refactored):
  - Client singleton via utils.clients
  - Safe JSON parsing via parse_llm_json (bracket-counting)
  - Structured logging + typed error handling
"""

import json
import logging
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from utils.clients import get_langchain_openai, parse_llm_json
from utils.puppeteer_runner import render_html_to_png

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Prompt
# ------------------------------------------------------------------------------
_CHARTJS_PROMPT = """\
이 차트/그래프 이미지를 분석하고 Chart.js 설정 객체로 정확히 변환하세요.
추가 텍스트 없이 ```json 블록 안에 JSON만 반환하세요.

━━━ 출력 형식 ━━━

```json
{
  "title": "차트 제목 (원본 언어 그대로)",
  "chartjs_config": {
    "type": "bar",
    "data": {
      "labels": ["항목1", "항목2", "항목3"],
      "datasets": [{
        "label": "데이터셋명",
        "data": [10, 20, 30],
        "backgroundColor": ["#4e79a7", "#f28e2b", "#e15759"]
      }]
    },
    "options": {
      "responsive": true,
      "plugins": {
        "legend": {"position": "top"},
        "title": {"display": true, "text": "차트 제목"}
      },
      "scales": {
        "y": {"beginAtZero": true, "title": {"display": true, "text": "Y축 라벨"}},
        "x": {"title": {"display": true, "text": "X축 라벨"}}
      }
    }
  }
}
```

━━━ 차트 타입 선택 ━━━
- bar: 막대 그래프 (수직/수평)
- line: 선 그래프 (시계열, 추세)
- pie: 원형 차트 (비율, 구성)
- doughnut: 도넛 차트
- radar: 레이더/방사형 차트
- scatter: 산점도

━━━ 데이터 추출 규칙 ━━━
1. **수치 정확성**: 눈금/축 값을 기준으로 데이터 값을 최대한 정확하게 읽어내세요
   - 막대 높이, 선의 꼭짓점, 파이 비율을 눈금 기준으로 정밀하게 추정
2. **라벨 보존**: 원본의 모든 라벨(축, 범례, 데이터 포인트)을 원본 언어 그대로 보존
3. **색상 재현**: 원본 색상이 식별 가능하면 유사한 hex 코드 사용, 불가능하면 구분 가능한 기본 팔레트 사용
4. **다중 데이터셋**: 여러 계열이 있으면 각각 별도 dataset으로 분리, 범례명 정확히 기재
5. **축 설정**: Y축 시작값(beginAtZero), 축 라벨, 눈금 간격이 원본과 유사하도록
6. **누락 금지**: 원본에 있는 모든 데이터 포인트를 빠짐없이 포함

━━━ 스타일 규칙 ━━━
- 수평 막대: type "bar" + options.indexAxis: "y"
- 선 그래프 점 표시: pointRadius: 4, pointBackgroundColor 설정
- 파이/도넛: backgroundColor 배열로 각 조각 색상 지정
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ margin: 20px; font-family: sans-serif; }}
    h3 {{ margin-bottom: 12px; }}
    .chart-wrap {{ max-width: 600px; margin: 0 auto; }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</head>
<body>
  <h3>{title}</h3>
  <div class="chart-wrap">
    <canvas id="chart"></canvas>
  </div>
  <script>
    (function() {{
      const ctx = document.getElementById('chart').getContext('2d');
      new Chart(ctx, {config});
    }})();
  </script>
</body>
</html>"""


@tool
def render_chartjs(image_b64: str, index: int) -> dict:
    """
    Convert a graph/chart image to Chart.js JSON config, then render to PNG via Puppeteer.
    GPT-4o extracts numeric data to generate a Chart.js config, and
    Puppeteer captures the HTML canvas as a PNG image.

    Args:
        image_b64: Base64-encoded PNG image.
        index: Source image index (for placeholder matching in assemble_pdf).

    Returns:
        {"index": int, "strategy": "chartjs", "base64_png": str}
        On failure, strategy falls back to "preserve_original".
    """
    llm = get_langchain_openai("gpt-4o")
    content = [
        {"type": "text", "text": _CHARTJS_PROMPT},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
    ]

    try:
        response = llm.invoke([HumanMessage(content=content)])
        text = response.content or ""
        parsed = parse_llm_json(text)

        if not isinstance(parsed, dict) or "chartjs_config" not in parsed:
            raise ValueError(f"chartjs_config missing: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")

        title = parsed.get("title", "chart")
        config = json.dumps(parsed["chartjs_config"], ensure_ascii=False)

        html = _HTML_TEMPLATE.format(title=title, config=config)
        png_b64 = render_html_to_png(html, timeout=30)

        logger.info(f"[chartjs] index={index}: render success")
        return {"index": index, "strategy": "chartjs", "base64_png": png_b64}

    except json.JSONDecodeError as e:
        logger.error(f"[chartjs] index={index}: JSON parse failed ({e}) → fallback")
        return {"index": index, "strategy": "preserve_original", "base64_png": image_b64}

    except Exception as e:
        logger.error(f"[chartjs] index={index}: failed ({type(e).__name__}: {e}) → fallback")
        return {"index": index, "strategy": "preserve_original", "base64_png": image_b64}