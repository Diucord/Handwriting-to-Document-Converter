import os
import asyncio
import base64
import logging
import shutil
from typing import Optional

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Browser executable resolution
# ------------------------------------------------------------------------------
# 우선순위:
# 1) 환경변수 CHROME_PATH / CHROMIUM_PATH / PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
# 2) 시스템 PATH 상의 브라우저
# 3) 없으면 Playwright 설치본 사용
_ENV_BROWSER_KEYS = [
    "CHROME_PATH",
    "CHROMIUM_PATH",
    "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH",
]

_CANDIDATE_BINARIES = [
    "chrome",
    "chrome.exe",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "msedge",
    "msedge.exe",
]


def _get_browser_executable_path() -> Optional[str]:
    for key in _ENV_BROWSER_KEYS:
        value = (os.getenv(key) or "").strip()
        if value:
            if os.path.exists(value):
                return value
            logger.warning(
                "[puppeteer_runner] %s is set but path does not exist: %s",
                key,
                value,
            )

    for name in _CANDIDATE_BINARIES:
        found = shutil.which(name)
        if found:
            return found

    return None


_BROWSER_EXECUTABLE = _get_browser_executable_path()

# ------------------------------------------------------------------------------
# Chromium launch args
# ------------------------------------------------------------------------------
_DEFAULT_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--font-render-hinting=none",
]

_JS_RENDER_WAIT_MS = 2000


def _normalize_error_message(e: Exception) -> str:
    msg = str(e)
    lowered = msg.lower()

    if "executable doesn't exist" in lowered or "browsertype.launch" in lowered:
        return (
            "브라우저 실행 파일을 찾지 못했습니다. "
            "'python -m playwright install chromium'를 실행하거나, "
            "CHROME_PATH 또는 CHROMIUM_PATH 환경변수에 브라우저 경로를 지정하세요."
        )

    if "failed to launch" in lowered:
        return (
            "브라우저 실행에 실패했습니다. "
            "서버 환경의 sandbox 제약 또는 브라우저 미설치 문제일 가능성이 큽니다."
        )

    return msg


async def _render(
    html: str,
    output_format: str,
    output_path: Optional[str],
    timeout: int,
    extra_args: list[str],
) -> bytes:
    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": _DEFAULT_ARGS + extra_args,
        }

        if _BROWSER_EXECUTABLE:
            launch_kwargs["executable_path"] = _BROWSER_EXECUTABLE

        browser = await p.chromium.launch(**launch_kwargs)
        try:
            page = await browser.new_page()
            page.set_default_timeout(timeout * 1000)

            await page.set_content(html, wait_until="networkidle")
            await page.wait_for_timeout(_JS_RENDER_WAIT_MS)

            try:
                await page.wait_for_function(
                    "window.renderFinished === true",
                    timeout=timeout * 1000,
                )
            except Exception:
                pass

            if output_format == "pdf":
                pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "20mm",
                        "right": "15mm",
                        "bottom": "20mm",
                        "left": "15mm",
                    },
                )

                if output_path:
                    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(pdf_bytes)

                return pdf_bytes

            png_bytes = await page.screenshot(
                full_page=True,
                type="png",
            )
            return png_bytes

        finally:
            await browser.close()


def _run_async(coro):
    """
    비동기 코루틴을 동기적으로 실행한다.
    이미 실행 중인 이벤트 루프가 있으면 nest_asyncio를 시도한다.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError as e:
            raise RuntimeError(
                "이미 실행 중인 이벤트 루프가 감지되었습니다. "
                "pip install nest_asyncio 를 실행하세요."
            ) from e

        return asyncio.get_event_loop().run_until_complete(coro)

    return asyncio.run(coro)


def render_html_to_pdf(
    html: str,
    output_path: str,
    timeout: int = 60,
    extra_args: Optional[list[str]] = None,
) -> str:
    """
    HTML 문자열을 A4 PDF로 렌더링한다.
    """
    if extra_args is None:
        extra_args = []

    try:
        _run_async(_render(html, "pdf", output_path, timeout, extra_args))
        logger.info(
            "[puppeteer_runner] PDF 생성 완료: %s (browser=%s)",
            output_path,
            _BROWSER_EXECUTABLE or "playwright-managed",
        )
        return os.path.abspath(output_path)

    except Exception as e:
        normalized = _normalize_error_message(e)
        logger.error(
            "[puppeteer_runner] PDF 생성 실패 (browser=%s): %s",
            _BROWSER_EXECUTABLE or "playwright-managed",
            normalized,
        )
        raise RuntimeError(f"PDF 렌더링 실패: {normalized}") from e


def render_html_to_png(
    html: str,
    timeout: int = 30,
    extra_args: Optional[list[str]] = None,
) -> str:
    """
    HTML 문자열을 full-page PNG 스크린샷으로 렌더링해 base64로 반환한다.
    """
    if extra_args is None:
        extra_args = []

    try:
        png_bytes = _run_async(_render(html, "png", None, timeout, extra_args))
        result = base64.b64encode(png_bytes).decode("utf-8")

        logger.info(
            "[puppeteer_runner] PNG 렌더링 완료 (크기=%s bytes, browser=%s)",
            len(png_bytes),
            _BROWSER_EXECUTABLE or "playwright-managed",
        )
        return result

    except Exception as e:
        normalized = _normalize_error_message(e)
        logger.error(
            "[puppeteer_runner] PNG 렌더링 실패 (browser=%s): %s",
            _BROWSER_EXECUTABLE or "playwright-managed",
            normalized,
        )
        raise RuntimeError(f"PNG 렌더링 실패: {normalized}") from e