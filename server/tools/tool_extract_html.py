"""
extract_html.py

Purpose:
- Extract clean HTML from a single document page image.
- Replace non-text visual regions with placeholder markers and return cropped images for those regions.

Design decisions:
- This tool is optimized for handwritten or unstructured notes pages, not for full visual redraw.
- Non-text visual elements must not be reconstructed as HTML, ASCII, SVG, or pseudo-layout text.
- Mathematical expressions are preserved as LaTeX so they can be rendered later in assemble_pdf.
- Placeholder markers may include bounding box coordinates, which are parsed to crop visual subregions.
- If placeholder cropping fails or coordinates are missing, the original full-page image is used as fallback.
- If text density is too low and no placeholders are detected, preserve_original is safer than forcing html_css output.

Supported output strategies:
- html_css
- preserve_original
"""

import os
import io
import re
import base64
import logging
from langchain_core.tools import tool
from utils.clients import get_genai_client

logger = logging.getLogger(__name__)

try:
    import PIL.Image
    from PIL import ImageEnhance, ImageFilter, ImageOps
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# 추출에 쓸 모델. 환경변수로 올리고 내릴 수 있다.
_EXTRACT_MODEL = os.getenv("MODEL_EXTRACT", "").strip() or "gemini-2.5-flash"

# 모델로 보낼 이미지의 긴 변 상한(px). utils.clients 와 같은 기본값을 쓴다.
_MAX_SEND_SIDE = int(os.getenv("MAX_IMAGE_SIDE", "1536"))


def _downscale_for_model(pil_img: "PIL.Image.Image") -> "PIL.Image.Image":
    """모델 전송용으로만 축소한다. 원본은 크롭에 계속 쓰이므로 건드리지 않는다."""
    try:
        w, h = pil_img.size
        longest = max(w, h)
        if longest <= _MAX_SEND_SIDE:
            return pil_img
        ratio = _MAX_SEND_SIDE / float(longest)
        out = pil_img.resize(
            (max(1, int(w * ratio)), max(1, int(h * ratio))), PIL.Image.LANCZOS
        )
        logger.info("[extract_html] 전송용 축소 %sx%s -> %sx%s", w, h, out.width, out.height)
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("[extract_html] 축소 실패, 원본 전송: %s", exc)
        return pil_img


def _log_gemini_usage(response) -> None:
    """Gemini 응답의 토큰 사용량을 남긴다."""
    try:
        u = getattr(response, "usage_metadata", None)
        if not u:
            return
        logger.info(
            "[usage] extract input=%s output=%s total=%s",
            getattr(u, "prompt_token_count", None),
            getattr(u, "candidates_token_count", None),
            getattr(u, "total_token_count", None),
        )
    except Exception:  # noqa: BLE001
        pass


def _preprocess_image(pil_img: "PIL.Image.Image") -> "PIL.Image.Image":
    """
    Preprocess handwritten note image for better AI analysis.

    Steps:
    1. Auto-contrast: normalize brightness/exposure differences
    2. Median filter: reduce camera noise while preserving edges
    3. Sharpening: make handwritten text crisper
    4. Contrast boost: improve ink vs background separation
    """
    try:
        img = pil_img.copy()
        # 1. Auto-contrast — normalize uneven lighting
        img = ImageOps.autocontrast(img, cutoff=1)
        # 2. Light denoise — remove sensor noise without blurring text
        img = img.filter(ImageFilter.MedianFilter(size=3))
        # 3. Sharpen — make strokes crisper for OCR
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        # 4. Contrast boost — separate ink from paper background
        img = ImageEnhance.Contrast(img).enhance(1.2)
        return img
    except Exception:
        return pil_img

# ------------------------------------------------------------------------------
# Prompt
# ------------------------------------------------------------------------------
_PROMPT = """\
당신은 최고 수준의 문서 디지털화 엔진입니다.
손글씨/비정형 노트 이미지를 깔끔하고 정확한 HTML로 변환하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 1단계: 이미지 전체 스캔 (먼저 수행)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
변환을 시작하기 전에, 이미지를 위→아래, 왼→오른쪽으로 완전히 스캔하세요.
- 페이지에 있는 모든 텍스트, 수식, 시각 요소의 위치를 파악하세요
- 어떤 영역이 텍스트이고, 어떤 영역이 그림/도형인지 구분하세요
- 페이지 가장자리, 여백, 다이어그램 사이의 텍스트도 놓치지 마세요

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 2단계: 시각 요소 → 플레이스홀더 변환
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 반드시 플레이스홀더로 대체해야 하는 것:
도형/그림이 포함된 모든 영역을 플레이스홀더로 만드세요. 적극적으로 만드세요!
- 다이어그램, 일러스트, 차트, 그래프
- 원자/분자 구조도, 회로도, 좌표계, 기하학적 도형
- 화살표+도형으로 구성된 개념도, 힘의 방향도
- 정전기 유도 도식, 전하 분포도 등 과학 시각 요소
- 모든 손으로 그린 스케치/도식
- 도형+텍스트 라벨이 함께 있는 영역 → 플레이스홀더! (텍스트로 추출하지 마세요)
- 화살표와 기호가 포함된 구조적 영역 → 플레이스홀더!

⚠ 판단 기준: 도형/화살표/기호가 하나라도 있으면 → 플레이스홀더로 만드세요.
텍스트 라벨이 붙어있어도 도형이 있으면 반드시 플레이스홀더입니다.

### 텍스트로만 추출할 것 (플레이스홀더 아님):
도형이 전혀 없고 순수 텍스트만 있는 영역만 해당:
- 순수 텍스트 문단 (도형 없음) → HTML 텍스트
- 수식만 있는 영역 (도형 없음) → LaTeX
- 순수 텍스트 표 → <table>
- 번호 목록, 개조식 정리 → <ol>/<ul>

### 완전히 무시할 것 (HTML에 포함하지 마세요):
- 장식용 캐릭터, 이모티콘, 낙서, 스티커 (시나모롤, 산리오, 귀여운 동물 등)
- 학습 내용과 무관한 꾸미기 요소, 노트 가장자리 장식

### 플레이스홀더 형식:
[IMAGE_PLACE_HOLDER_N|top,left,bottom,right]

- N: 0부터 순차 증가
- top, left, bottom, right: 이미지 크기 대비 백분율 좌표 (0-100)
- 예시: [IMAGE_PLACE_HOLDER_0|20,5,55,95] = 세로 20%~55%, 가로 5%~95%
- 바운딩 박스는 시각 요소를 꽉 채우도록 정확하게 잡으세요 (너무 크거나 작지 않게)

### 시각 요소 재현 금지:
절대로 그림을 텍스트/ASCII 아트/SVG/텍스트 테이블로 흉내 내지 마세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 3단계: 텍스트 추출 및 교정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 교정 규칙 (정확성 최우선):
- 문맥 기반으로 필기 인식 오류를 교정하되, 원문 의미를 보존하세요
- 수학 공식: 독립 수식 $$...$$, 인라인 수식 $...$
- 분수: \\frac{a}{b}, 지수: x^2, 아래첨자: x_1, 루트: \\sqrt{x}
- 한글 맞춤법과 띄어쓰기 교정

**과학/수학 용어 교정 (필수 확인 항목):**
손글씨 인식에서 자주 발생하는 혼동 패턴을 반드시 교정하세요:
- 정↔전 혼동: "정기력" → "전기력", "정전기" (O) "정정기" (X)
- 기↔지 혼동: "전지력" → "전기력"
- 력↔럭 혼동: "인럭" → "인력"
- 인↔인 혼동: "인럭" → "인력", "척럭" → "척력"
- 확인 필수 용어 목록: 전기력, 인력, 척력, 정전기, 대전체, 도체, 부도체,
  원자, 전자, 양성자, 중성자, 전하, 쿨롱, 유전체, 절연체, 전위, 전압,
  저항, 전류, 자기력, 자기장, 전자기, 파동, 진동수, 파장, 진폭

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 4단계: HTML 구조화
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 메인 제목 → <h1>, 하위 섹션 → <h2>/<h3>
2. 글머리 기호/번호 → <ul><li> 또는 <ol><li>
3. 관련 줄 → <p> 블록으로 결합
4. 텍스트 표 → <table>
5. 강조 → <strong>(굵게), <em>(기울임), <u>(밑줄)
6. HTML body 내용만 반환 (<html>/<head>/<body> 태그 불포함)
7. 빈 <p> 태그 사용 금지

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 5단계: 최종 검증 (반드시 수행)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 전에 원본 이미지를 다시 한번 대조하세요:
✓ 이미지의 모든 텍스트가 HTML에 포함되었는가?
✓ 다이어그램 주변/사이의 텍스트도 빠짐없이 추출했는가?
✓ 페이지 상단/하단/좌측/우측 가장자리의 텍스트도 포함했는가?
✓ 줄 번호, 주석, 괄호 안 텍스트, 화살표 옆 텍스트가 모두 있는가?
✓ 수식이 올바른 LaTeX 문법으로 변환되었는가?
✓ 과학 용어 오타가 없는가?
✓ 플레이스홀더 바운딩 박스가 시각 요소를 정확히 감싸는가?

누락된 내용이 발견되면 반드시 추가한 후 출력하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 특수 케이스
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
페이지가 거의 전부 다이어그램이고 텍스트가 거의 없는 경우:
[IMAGE_PLACE_HOLDER_0|0,0,100,100]
"""

# Matches [IMAGE_PLACE_HOLDER_N|top,left,bottom,right] or [IMAGE_PLACE_HOLDER_N]
_PH_PATTERN = re.compile(
    r"\[IMAGE_PLACE_HOLDER_(\d+)(?:\|(\d+),(\d+),(\d+),(\d+))?\]"
)


def _clean_html(raw: str) -> str:
    html = (raw or "").replace("\r", "").strip()
    html = re.sub(r"^```(?:html)?\s*", "", html, flags=re.I)
    html = re.sub(r"\s*```$", "", html)
    html = re.sub(r"</?mjx[^>]*>", "", html, flags=re.I)
    html = re.sub(r"<p>\s*</p>", "", html)
    html = re.sub(r"(<br\s*/?>\s*){2,}", "</p><p>", html)
    html = re.sub(r"<p>\s*<h", "<h", html)
    return html.strip()


def _parse_placeholders(html: str, pil_img: "PIL.Image.Image", image_b64: str):
    """
    Parse placeholder markers from HTML, crop diagram regions.

    Returns:
        indices: list of placeholder indices
        images: dict mapping str(index) -> cropped base64 PNG
        bboxes: dict mapping str(index) -> {"width_pct": float, "height_pct": float}
        cleaned_html: HTML with bbox info stripped from placeholders
    """
    indices = []
    images = {}
    bboxes = {}
    w, h = pil_img.size

    for m in _PH_PATTERN.finditer(html or ""):
        idx = int(m.group(1))
        indices.append(idx)

        if m.group(2) is not None:
            top_pct = max(0, min(100, int(m.group(2))))
            left_pct = max(0, min(100, int(m.group(3))))
            bottom_pct = max(0, min(100, int(m.group(4))))
            right_pct = max(0, min(100, int(m.group(5))))

            if bottom_pct > top_pct and right_pct > left_pct:
                # Store bbox proportions for natural width sizing
                bboxes[str(idx)] = {
                    "width_pct": right_pct - left_pct,
                    "height_pct": bottom_pct - top_pct,
                }

                pad_y = int(h * 0.02)
                pad_x = int(w * 0.02)
                top = max(0, int(h * top_pct / 100) - pad_y)
                left = max(0, int(w * left_pct / 100) - pad_x)
                bottom = min(h, int(h * bottom_pct / 100) + pad_y)
                right = min(w, int(w * right_pct / 100) + pad_x)

                try:
                    cropped = pil_img.crop((left, top, right, bottom))
                    cropped = _preprocess_image(cropped)
                    buf = io.BytesIO()
                    cropped.save(buf, format="PNG", optimize=True)
                    images[str(idx)] = base64.b64encode(buf.getvalue()).decode()
                    continue
                except Exception:
                    pass

        # Fallback: no bbox or crop failed -> use full page
        images[str(idx)] = image_b64

    # Strip bbox from placeholders: [IMAGE_PLACE_HOLDER_N|...] -> [IMAGE_PLACE_HOLDER_N]
    cleaned = _PH_PATTERN.sub(
        lambda m: f"[IMAGE_PLACE_HOLDER_{m.group(1)}]", html or ""
    )

    return indices, images, bboxes, cleaned


@tool
def extract_html(image_b64: str, index: int) -> dict:
    """Extract HTML content and image placeholder metadata from a single page image."""

    if not _PIL_AVAILABLE or not image_b64:
        raise ValueError("Pillow package is required or image_b64 is empty.")

    try:
        client = get_genai_client()
        img_bytes = base64.b64decode(image_b64)
        pil_img = PIL.Image.open(io.BytesIO(img_bytes)).convert("RGB")

        # Preprocess for cleaner AI analysis
        processed_img = _preprocess_image(pil_img)

        # 모델에 보낼 이미지만 축소한다.
        #
        # 원본(pil_img)은 아래 _parse_placeholders 에서 영역을 잘라낼 때
        # 그대로 써야 하므로 건드리지 않는다. 축소본은 전송용이다.
        # 리사이즈가 없던 시절에는 폰카 원본(4000px급)이 그대로 올라가
        # 비전 토큰의 대부분을 차지했다.
        sent_img = _downscale_for_model(processed_img)

        response = client.models.generate_content(
            model=_EXTRACT_MODEL,
            contents=[_PROMPT, sent_img],
        )

        _log_gemini_usage(response)

        html = _clean_html(response.text or "")
        placeholders, placeholder_images, placeholder_bboxes, html = _parse_placeholders(
            html, pil_img, image_b64
        )

        text_only = re.sub(r"<[^>]+>", "", html).strip()
        if not placeholders and len(text_only) < 50:
            logger.info(
                "[extract_html] index=%s: low text density -> preserve_original",
                index,
            )
            return {
                "index": index,
                "strategy": "preserve_original",
                "html_text": "",
                "placeholder_indices": [],
                "placeholder_images": {},
                "original_b64": image_b64,
            }

        logger.info(
            "[extract_html] index=%s html_len=%s placeholders=%s cropped=%s",
            index, len(html), len(placeholders),
            sum(1 for v in placeholder_images.values() if v != image_b64),
        )

        return {
            "index": index,
            "strategy": "html_css",
            "html_text": html,
            "placeholder_indices": placeholders,
            "placeholder_images": placeholder_images,
            "placeholder_bboxes": placeholder_bboxes,
            "original_b64": image_b64,
        }

    except Exception as e:
        logger.error("[extract_html] index=%s failed: %s", index, e)
        return {
            "index": index,
            "strategy": "preserve_original",
            "html_text": "",
            "placeholder_indices": [],
            "placeholder_images": {},
            "original_b64": image_b64,
        }
