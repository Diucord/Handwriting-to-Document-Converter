# Notaformat — 페이지 사진을 리포트로 변환하는 에이전트 파이프라인

손으로 쓴 노트나 문서를 사진으로 올리면, 본문은 구조화된 HTML 로 복원하고
그림은 종류를 판별해 다시 그린 뒤 A4 PDF 로 조립합니다.

**Live:** https://notaformat.vercel.app/

---

## 무엇을 해결하는가

문서 사진을 텍스트로 옮기는 일은 OCR 로 해결됩니다. 남는 문제는 그림입니다.

페이지에서 차트나 도식을 오려내 그대로 붙이면 결과물에는 이미지가 남습니다.
선택도 검색도 되지 않고, 확대하면 깨지며, 원본 사진의 기울기와 그림자를
그대로 가져옵니다. 문서를 다시 만든 것이 아니라 사진을 옮긴 것이 됩니다.

Notaformat 은 그림을 오려내지 않습니다. 영역마다 무엇인지 먼저 판별하고,
종류에 맞는 렌더러로 다시 그립니다. 수식은 LaTeX, 순서도는 Mermaid,
데이터 차트는 Chart.js 로 재생성되므로 결과물이 텍스트와 벡터로 남습니다.

---

## 어떻게 동작하는가

LangGraph `StateGraph` 로 네 단계를 실행합니다.

```
 페이지 이미지 ─► extract ─► classify ─► render ─► assemble ─► PDF
                    │           │          │          │
                  본문을      영역별     종류별     HTML 합치고
                  구조화      렌더 전략   렌더러로   Playwright 로
                  HTML 로     판정        재생성     A4 인쇄
                  복원
```

| 단계 | 하는 일 |
|---|---|
| `extract` | 이미지에서 본문을 구조화 HTML 로 복원. 그림 자리에는 좌표를 담은 자리표시자 `[IMAGE_PLACE_HOLDER_N\|top,left,bottom,right]` 를 남깁니다 |
| `classify` | 각 영역이 수식 / 순서도 / 데이터 차트 / 삽화 / 원본보존 중 무엇인지 판정 |
| `render` | 판정 결과에 따라 5개 렌더러 중 하나로 보내 다시 그림 |
| `assemble` | 자리표시자를 렌더 결과로 치환하고 Playwright 로 A4 PDF 생성 |

그래프 노드는 셋(`extract_pages` → `classify_and_render` → `assemble_document`)이고,
`classify` 와 `render` 는 한 노드 안에서 이어집니다. 진행률 표시는 사용자가 보는
단위인 네 단계(`STAGES`)로 내보냅니다.

### 렌더러

| 판정 | 렌더러 | 산출물 |
|---|---|---|
| 수식 | `tool_render_math` | LaTeX → KaTeX |
| 순서도 · 구조도 | `tool_render_mermaid` | Mermaid 정의 |
| 데이터 차트 | `tool_render_chartjs` | Chart.js 설정 |
| 삽화 | `tool_render_illustration` | SVG |
| 사진 · 재생성 불가 | `tool_preserve_original` | 원본 영역 크롭 |

마지막 항목이 있는 이유는, 모든 그림을 다시 그릴 수 있는 것은 아니기 때문입니다.
사진이나 손그림처럼 재생성이 의미 없는 영역은 판정 단계에서 걸러 원본을 씁니다.

### 작업별 모델 등급

한 모델로 전부 처리하지 않고 작업 성격에 맞춰 나눕니다
(`server/utils/clients.py`).

| 작업 | 기본 모델 | temperature | 이유 |
|---|---|---|---|
| `classify` | `gpt-4o-mini` | 0.0 | 5개 라벨 중 하나를 고르는 작업. 영역 수만큼 호출되므로 비용에 가장 민감합니다 |
| `generate` | `gpt-4o` | 0.2 | mermaid · chartjs · latex 코드를 만들어야 하므로 추론 품질이 필요합니다 |
| `vision` | `gpt-4o` | 0.1 | 이미지에서 구조를 읽어내는 작업 |

`MODEL_CLASSIFY` / `MODEL_GENERATE` / `MODEL_VISION` 환경변수로 각각 올릴 수 있습니다.
분류를 낮은 등급으로 내린 것이 비전 토큰 절감의 대부분을 차지합니다.

렌더는 `ThreadPoolExecutor` 워커 4개로 병렬 처리합니다.

---

## 스택

| 영역 | 사용 기술 |
|---|---|
| 오케스트레이션 | LangGraph `StateGraph`, LangChain |
| 모델 | OpenAI (`langchain-openai`), Google Gen AI (`langchain-google-genai`) |
| 백엔드 | FastAPI, Uvicorn |
| 렌더링 | Playwright (HTML → A4 PDF), KaTeX, Mermaid, Chart.js |
| 프런트엔드 | React 19, Vite, TypeScript |
| DB · 인증 | SQLAlchemy, PostgreSQL(배포) / MySQL(로컬), python-jose, passlib |
| 배포 | Fly.io (도쿄 `nrt`) + 영구 볼륨, Docker |

---

## 실행

```bash
# 백엔드
pip install -r requirements.txt
playwright install chromium
uvicorn server.main:app --reload

# 프런트엔드
cd client
npm install
npm run dev
```

환경변수는 `.env` 에 둡니다. 최소 `OPENAI_API_KEY` 가 필요하며,
모델 등급은 위의 `MODEL_*` 로 조정합니다.

---

## 배포

Fly.io 도쿄 리전에 배포하고, 변환 산출물은 영구 볼륨에 씁니다.
컨테이너 로컬에 쓰면 재시작할 때 사라지기 때문입니다.

```bash
flyctl launch --no-deploy --copy-config
flyctl secrets set OPENAI_API_KEY=...
flyctl volumes create notaformat_data --size 3 --region nrt
flyctl deploy
```

자세한 절차는 `DEPLOY.md` 를 참고합니다.

---

## 저장소 구성

```
server/
  agents/
    orchestrator_agent.py   StateGraph 정의, 진행률(STAGES), 병렬 렌더
    state.py                단계 간 전달되는 상태 객체
  tools/
    tool_extract_html.py    이미지 → 구조화 HTML + 자리표시자
    tool_classify_image.py  영역별 렌더 전략 판정
    tool_render_*.py        판정별 렌더러 4종
    tool_preserve_original.py  재생성하지 않는 영역의 원본 크롭
    tool_assemble_pdf.py    치환 + Playwright A4 인쇄
  routers/                  FastAPI 라우터
  utils/clients.py          작업별 모델 등급 프로파일
client/                     React 19 + Vite 프런트엔드
```

---

## 기록

설계 판단의 배경은 블로그에 정리했습니다.

- [단일 함수에서 에이전트 파이프라인으로: 손글씨 문서 변환기의 재설계](https://sy-dashboard-77n.pages.dev/blog/monolith-to-agent-pipeline)
- [진행률 막대 하나로는 설명되지 않는 작업: 파이프라인을 그대로 드러낸 UI 재설계](https://sy-dashboard-77n.pages.dev/blog/ui-that-shows-the-pipeline)
