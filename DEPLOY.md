# 배포 안내

Notaformat 백엔드(FastAPI + LangGraph)를 컨테이너로 올리는 방법입니다.

## 왜 Docker 인가

이 서버는 서버리스(Vercel Functions 등)에 그대로 올릴 수 없습니다. 이유가 세 가지입니다.

1. **Chromium 이 필요합니다.** PDF·PNG 렌더링을 Playwright 로 하기 때문에
   실행 환경에 브라우저 바이너리가 있어야 합니다.
2. **변환 결과를 디스크에 씁니다.** `server/converted`, `server/uploads` 를
   정적 파일로 서빙합니다. 서버리스는 요청 간 디스크가 유지되지 않습니다.
3. **작업이 길게 돕니다.** 페이지 수에 따라 수십 초가 걸리므로 짧은
   실행 시간 제한에 걸립니다.

Docker 이미지로 만들면 Railway·Render·Fly.io 어디에 올리든 동일하게 동작하고,
로컬에서 같은 방식으로 검증할 수 있습니다.

## 로컬 개발 (Docker 없이)

백엔드와 프런트를 **명령 하나로** 함께 띄웁니다.

```bash
npm run setup    # 최초 1회 — Python 패키지 + npm 의존성 설치
npm run dev      # 백엔드(4000) + 프런트(5173) 동시 실행
```

`http://localhost:5173` 이 개발용 화면입니다. Vite 가 `/api` 와 `/converted`
요청을 4000 포트로 프록시하므로 별도 설정이 필요 없습니다.

| 스크립트 | 하는 일 |
|---|---|
| `npm run dev` | 두 서버를 함께 실행. Ctrl+C 한 번에 둘 다 종료(`-k`) |
| `npm run dev:server` | 백엔드만 (uvicorn, 포트 4000, 자동 리로드) |
| `npm run dev:client` | 프런트만 (vite, 포트 5173) |

### 사전 조건

- **MySQL 이 떠 있어야 합니다.** `server/.env` 의 `DATABASE_URL` 이 로컬 MySQL 을
  가리킵니다. 서버가 없으면 기동 시 접속 오류가 납니다. MySQL 없이 돌리려면
  `DATABASE_URL` 을 비우세요 — SQLite 파일로 자동 전환됩니다.
- **Python 의존성은 `requirements.txt` 로 설치합니다.** 이걸 건너뛰면
  `ModuleNotFoundError: No module named 'pymysql'` (또는 `jose`) 로 기동이
  실패합니다. 두 패키지 모두 requirements 에 있으니 `npm run setup` 이면 됩니다.

## Docker 로 확인

```bash
# 1) 환경변수 준비
cp .env.example .env      # GEMINI_API_KEY, JWT_SECRET_KEY 채우기

# 2) 이미지 빌드
docker build -t notaformat .

# 3) 실행
docker run --rm -p 8000:8000 --env-file .env notaformat
```

`http://localhost:8000/docs` 에서 API 문서가 뜨면 정상입니다.

## 이미지 구성

| 항목 | 선택 | 이유 |
|---|---|---|
| 베이스 | `mcr.microsoft.com/playwright/python` | Chromium 과 의존 라이브러리가 포함되어 있음 |
| 폰트 | `fonts-noto-cjk` 추가 설치 | 없으면 PDF 안의 한글이 전부 네모로 나옴 |
| 포트 | `${PORT}` (기본 8000) | 호스팅 업체가 주입하는 포트를 그대로 사용 |

Node.js 는 넣지 않았습니다. `server/render.js` 와 `puppeteer` 의존성이 남아
있지만 현재 코드는 Python Playwright 만 사용합니다.

## 데이터 보존

컨테이너는 재시작하면 파일이 초기화됩니다. 다음 두 가지는 별도 처리가 필요합니다.

- **계정·변환 이력** — `DATABASE_URL` 에 외부 DB(MySQL·PostgreSQL)를 지정합니다.
  비워 두면 SQLite 파일로 동작하며, 재시작 시 사라집니다.
- **변환된 PDF** — `server/converted` 에 볼륨을 붙이거나, 오브젝트 스토리지로
  옮기는 작업이 필요합니다. (현재는 로컬 디스크에만 저장)

## 프런트엔드

`client/` 는 정적 빌드이므로 Vercel 등에 그대로 올릴 수 있습니다.
**빌드 전에 백엔드 주소를 지정해야 합니다.**

```bash
cd client
npm install
VITE_API_BASE_URL=https://your-backend-host npm run build   # dist/ 생성
```

지정하지 않으면 `http://<현재호스트>:4000` 을 호출하는데, HTTPS 로 서빙되는
페이지에서 HTTP 요청은 브라우저가 차단하므로 프로덕션에서는 반드시 넣어야 합니다.

## 남은 것

- 변환 산출물의 영구 저장소(S3 등) 연결
- `render.js` 와 puppeteer 의존성 정리 (현재 미사용)
