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

if not DATABASE_URL:
    # 컨테이너 재시작 시 초기화되므로, 계정·이력을 보존하려면
    # 이 파일 경로에 볼륨을 붙이거나 DATABASE_URL 을 지정합니다.
    _db_path = os.path.join(os.path.dirname(__file__), "notaformat.db")
    DATABASE_URL = f"sqlite:///{_db_path}"

# SQLite 는 기본적으로 생성 스레드에서만 쓸 수 있는데, FastAPI 는
# 여러 스레드에서 세션을 열기 때문에 이 옵션이 필요합니다.
_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
