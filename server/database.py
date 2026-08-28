from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL 이 없으면 SQLite 로 떨어집니다.
#
# 이전 기본값은 로컬 MySQL(root/password)이었는데, 그 상태로 다른 환경에
# 올리면 DB 가 없어 기동 자체가 실패합니다. 배포 시에는 DATABASE_URL 만
# 넣어 주면 MySQL·PostgreSQL 로 그대로 전환됩니다.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# 호스팅 업체가 넣어 주는 URL 은 드라이버 접두사가 없는 경우가 많습니다.
# Fly.io 의 `postgres attach` 는 `postgres://` 로 넣어 주는데, SQLAlchemy 2.x
# 는 이 접두사를 인식하지 못하므로 기동 시 예외가 납니다.
# 접속 정보를 사람이 다시 편집하지 않아도 되도록 여기서 정규화합니다.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

if not DATABASE_URL:
    # 컨테이너 재시작 시 초기화되므로, 계정·이력을 보존하려면
    # 이 파일 경로에 볼륨을 붙이거나 DATABASE_URL 을 지정합니다.
    _db_path = os.path.join(os.path.dirname(__file__), "notaformat.db")
    DATABASE_URL = f"sqlite:///{_db_path}"

if DATABASE_URL.startswith("sqlite"):
    # SQLite 는 기본적으로 생성 스레드에서만 쓸 수 있는데, FastAPI 는
    # 여러 스레드에서 세션을 열기 때문에 이 옵션이 필요합니다.
    _connect_args = {"check_same_thread": False}
elif DATABASE_URL.startswith("postgresql"):
    # 타임아웃이 없으면 DB 가 응답하지 않을 때 기동이 무한정 멈춥니다.
    # 재시도 로직이 동작하려면 연결 시도가 유한 시간 안에 끝나야 합니다.
    _connect_args = {"connect_timeout": 5}
else:
    _connect_args = {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
