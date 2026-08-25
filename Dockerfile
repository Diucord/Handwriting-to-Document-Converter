# Notaformat — 백엔드(FastAPI + LangGraph) 배포용 이미지
#
# PDF·PNG 렌더링에 Playwright(Chromium)를 쓰기 때문에 브라우저가 포함된
# 공식 Playwright 이미지를 베이스로 씁니다. 일반 python 이미지에서 시작하면
# Chromium 의존 라이브러리(폰트·libnss 등)를 직접 설치해야 합니다.
#
# 한글 문서를 렌더링하므로 한글 폰트를 별도로 넣습니다. 이게 없으면
# PDF 안의 한글이 전부 깨진 네모로 나옵니다.

FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 한글 폰트 (Noto Sans CJK) — PDF 한글 깨짐 방지
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 먼저 설치해 레이어 캐시를 살립니다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 베이스 이미지에 Chromium 이 이미 있지만, playwright 버전이 바뀌어도
# 안전하도록 한 번 더 확인합니다. (이미 있으면 빠르게 통과)
RUN python -m playwright install chromium

COPY server/ ./server/

WORKDIR /app/server

# 변환 산출물·업로드 디렉터리. 컨테이너는 재시작 시 초기화되므로
# 영구 보관이 필요하면 이 두 경로에 볼륨을 붙입니다.
RUN mkdir -p converted uploads

# 호스팅 업체가 넣어 주는 PORT 를 우선 사용하고, 없으면 8000
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
