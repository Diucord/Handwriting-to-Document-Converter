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
