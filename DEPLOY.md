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

## Fly.io 배포

백엔드는 Fly.io 에 올립니다. `fly.toml` 이 저장소에 있으므로 아래 순서만
따르면 됩니다.

### 1) flyctl 설치·로그인

```powershell
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

```bash
flyctl auth login
```

### 2) 앱 생성

```bash
cd ai_report_maker
flyctl launch --no-deploy --copy-config
```

`--copy-config` 를 붙여야 저장소의 `fly.toml` 을 그대로 씁니다. 빼면
flyctl 이 설정을 새로 만들면서 볼륨·메모리 설정이 사라집니다.

앱 이름이 이미 쓰이고 있으면 `fly.toml` 의 `app` 값을 바꿉니다.

### 3) 볼륨 생성

```bash
flyctl volumes create notaformat_data --size 3 --region nrt
```

변환한 PDF 를 담습니다. 이 볼륨이 없으면 재배포·재시작마다 산출물이
전부 사라집니다. 리전은 `fly.toml` 의 `primary_region` 과 같아야 합니다.

### 4) 환경변수 주입

```bash
flyctl secrets set   GEMINI_API_KEY="..."   OPENAI_API_KEY="..."   JWT_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"   DATABASE_URL=""
```

`DATABASE_URL` 을 비우면 SQLite 로 동작하며, 파일이 `/data` 볼륨 밖에
생기므로 재시작 시 계정·이력이 사라집니다. 계정을 유지하려면 외부
PostgreSQL 을 만들어 지정합니다.

```bash
flyctl postgres create --name notaformat-db --region nrt
flyctl postgres attach notaformat-db
```

`attach` 는 `DATABASE_URL` 을 자동으로 넣어 줍니다. 다만 드라이버 접두사가
`postgres://` 로 오므로, SQLAlchemy 가 읽도록 아래처럼 바꿔야 합니다.

```bash
flyctl secrets set DATABASE_URL="postgresql+psycopg://<attach 가 준 값의 나머지>"
```

### 5) 배포

```bash
flyctl deploy
```

`https://notaformat.fly.dev/docs` 가 뜨면 정상입니다.

### 6) 프런트엔드 연결

Vercel 프로젝트의 환경변수에 백엔드 주소를 넣고 재배포합니다.

```
VITE_API_BASE_URL = https://notaformat.fly.dev
```

이 값이 없으면 프런트가 `http://<현재호스트>:4000` 을 호출하는데, HTTPS
페이지에서 HTTP 요청은 브라우저가 차단하므로 변환이 동작하지 않습니다.

### 설정 근거

| 항목 | 값 | 이유 |
|---|---|---|
| 메모리 | 2GB | Chromium 렌더링에 1GB 로는 OOM 이 납니다 |
| `min_machines_running` | 1 | 변환이 수십 초라 콜드 스타트·중단을 피해야 합니다 |
| `auto_stop_machines` | false | 요청 도중 머신이 멈추면 변환이 통째로 버려집니다 |
| 동시 요청 | soft 8 / hard 12 | Chromium 이 메모리를 많이 써서 낮게 잡았습니다 |
| 리전 | `nrt` (도쿄) | 한국에서 가장 가깝습니다 |

### 확인

```bash
flyctl status          # 머신 상태
flyctl logs            # 실시간 로그
flyctl ssh console     # 컨테이너 접속
```

## 남은 것

- **Docker 이미지 빌드는 로컬에서 검증하지 못했습니다.** Docker Desktop 을
  띄운 뒤 `docker build -t notaformat .` 로 한 번 확인하는 편이 안전합니다.
  Playwright 베이스 이미지 태그(`v1.52.0-jammy`)와 `requirements.txt` 의
  playwright 버전이 어긋나면 이 단계에서 드러납니다.
- 계정·이력을 유지하려면 외부 PostgreSQL 연결이 필요합니다. SQLite 파일은
  `/data` 볼륨 밖에 생기므로 재시작 시 사라집니다.
- `render.js` 와 puppeteer 의존성 정리 (현재 미사용)
