from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    real_name = Column(String(100), nullable=False)
    nickname = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    profile_image_url = Column(String(500), default=None)
    is_verified = Column(Boolean, default=False)
    verify_code = Column(String(10), default=None)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    histories = relationship("ConversionHistory", back_populates="user")


class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # "pdf" or "docx"
    file_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="histories")


class SharedDocument(Base):
    """
    링크 공유.

    변환 결과 하나당 공유 링크 하나를 만듭니다. 링크를 받은 사람은
    로그인 없이 열 수 있으므로, token 은 추측할 수 없어야 합니다
    (secrets.token_urlsafe 로 생성).

    만료·다운로드 한도·비밀번호는 전부 선택입니다. 값이 없으면
    제한 없음으로 봅니다.
    """

    __tablename__ = "shared_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(64), nullable=False, unique=True, index=True)

    history_id = Column(Integer, ForeignKey("conversion_history.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 공유 시점의 값을 복사해 둡니다. 원본 이력이 지워져도 링크가
    # 살아 있는 동안에는 제목을 보여줄 수 있어야 합니다.
    title = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_url = Column(String(500), nullable=False)

    # 선택 제한 — None 이면 제한 없음
    expires_at = Column(DateTime, default=None)
    max_downloads = Column(Integer, default=None)
    password_hash = Column(String(255), default=None)

    download_count = Column(Integer, nullable=False, default=0)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User")
    history = relationship("ConversionHistory")
