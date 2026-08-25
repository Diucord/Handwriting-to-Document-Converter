import os
import re
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    SignupRequest, LoginRequest, ForgotPasswordRequest,
    UserResponse, UserUpdateRequest, TokenResponse,
    VerifyPhoneRequest,
)
from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user,
)
from email_utils import send_temp_password_email
from sms_utils import send_verification_sms

router = APIRouter(prefix="/api/auth", tags=["auth"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # 유효성 검사
    if not req.real_name.strip():
        raise HTTPException(status_code=400, detail="실명을 입력해주세요.")
    if not req.nickname.strip():
        raise HTTPException(status_code=400, detail="닉네임을 입력해주세요.")
    if not req.email.strip():
        raise HTTPException(status_code=400, detail="이메일을 입력해주세요.")
    if not req.phone_number.strip():
        raise HTTPException(status_code=400, detail="핸드폰 번호를 입력해주세요.")
    if req.password != req.password_confirm:
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")
    if len(req.password) > 20:
        raise HTTPException(status_code=400, detail="비밀번호는 20자 이하여야 합니다.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', req.password):
        raise HTTPException(status_code=400, detail="비밀번호에 특수문자를 1개 이상 포함해주세요.")

    # 중복 검사
    existing_email = db.query(User).filter(User.email == req.email).first()
    if existing_email and existing_email.is_verified:
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    if existing_email and not existing_email.is_verified:
        db.delete(existing_email)
        db.commit()

    existing_nickname = db.query(User).filter(User.nickname == req.nickname).first()
    if existing_nickname and existing_nickname.is_verified:
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")
    if existing_nickname and not existing_nickname.is_verified:
        db.delete(existing_nickname)
        db.commit()

    existing_phone = db.query(User).filter(User.phone_number == req.phone_number).first()
    if existing_phone and existing_phone.is_verified:
        raise HTTPException(status_code=400, detail="이미 가입된 핸드폰 번호입니다. 로그인해주세요.")
    if existing_phone and not existing_phone.is_verified:
        db.delete(existing_phone)
        db.commit()

    # 인증 코드 생성 (6자리 숫자)
    verify_code = "".join(secrets.choice(string.digits) for _ in range(6))

    user = User(
        real_name=req.real_name.strip(),
        nickname=req.nickname.strip(),
        email=req.email.strip(),
        phone_number=req.phone_number.strip(),
        password_hash=hash_password(req.password),
        is_verified=False,
        verify_code=verify_code,
    )
    db.add(user)
    db.commit()

    # SMS 인증번호 발송
    success = send_verification_sms(req.phone_number.strip(), verify_code)
    if not success:
        raise HTTPException(status_code=500, detail="인증번호 전송에 실패했습니다.")

    return {"message": "인증번호가 발송되었습니다.", "phone_number": req.phone_number.strip()}


@router.post("/verify-phone", response_model=TokenResponse)
def verify_phone(req: VerifyPhoneRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == req.phone_number).first()
    if not user:
        raise HTTPException(status_code=400, detail="사용자를 찾을 수 없습니다.")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="이미 인증된 계정입니다.")
    if user.verify_code != req.code:
        raise HTTPException(status_code=400, detail="인증번호가 올바르지 않습니다. 다시 확인해주세요.")

    user.is_verified = True
    user.verify_code = None
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="핸드폰 인증이 완료되지 않은 계정입니다.")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        return {"message": "등록된 이메일이라면 임시 비밀번호가 전송됩니다."}

    chars = string.ascii_letters + string.digits
    temp_password = "".join(secrets.choice(chars) for _ in range(8))

    user.password_hash = hash_password(temp_password)
    db.commit()

    success = send_temp_password_email(req.email, temp_password)
    if not success:
        raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다.")

    return {"message": "등록된 이메일이라면 임시 비밀번호가 전송됩니다."}


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    req: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.real_name is not None:
        user.real_name = req.real_name.strip()
    if req.nickname is not None:
        nickname = req.nickname.strip()
        existing = db.query(User).filter(User.nickname == nickname, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")
        user.nickname = nickname

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/profile-image", response_model=UserResponse)
async def upload_profile_image(
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    filename = f"profile_{user.id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)

    user.profile_image_url = f"/uploads/profiles/{filename}"
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)
