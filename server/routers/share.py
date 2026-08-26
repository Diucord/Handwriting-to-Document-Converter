"""
링크 공유.

변환한 문서에 링크를 만들어 로그인하지 않은 사람도 열 수 있게 합니다.

설계 메모
- 토큰은 secrets.token_urlsafe 로 만듭니다. 링크를 아는 사람은 누구나
  열 수 있으므로 추측 가능한 값(순번·UUID v1 등)을 쓰면 안 됩니다.
- 만료·다운로드 한도·비밀번호는 전부 선택입니다. None 이면 제한이 없습니다.
- 비밀번호는 평문으로 두지 않고 기존 auth 의 해시 함수를 그대로 씁니다.
- 조회(GET /s/{token})와 다운로드 확인(POST .../access)을 나눴습니다.
  조회만으로 다운로드 횟수가 깎이면, 링크를 열어보기만 해도 한도가
  소진되기 때문입니다.
"""

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user, hash_password, verify_password
from database import get_db
from models import ConversionHistory, SharedDocument, User

router = APIRouter(prefix="/api/share", tags=["share"])


# ── 스키마 ────────────────────────────────────────────────────────────────

class ShareCreate(BaseModel):
    history_id: int
    expires_in_days: int | None = Field(default=7, ge=1, le=365)
    max_downloads: int | None = Field(default=None, ge=1, le=10000)
    password: str | None = Field(default=None, min_length=1, max_length=128)


class ShareOut(BaseModel):
    token: str
    title: str
    file_type: str
    expires_at: datetime | None
    max_downloads: int | None
    download_count: int
    has_password: bool
    revoked: bool
    created_at: datetime | None

    class Config:
        from_attributes = True


class SharedView(BaseModel):
    """링크를 받은 사람에게 보여줄 정보. file_url 은 잠금이 풀려야 담깁니다."""
    title: str
    file_type: str
    expires_at: datetime | None
    requires_password: bool
    remaining_downloads: int | None
    file_url: str | None = None


class AccessBody(BaseModel):
    password: str | None = None


# ── 헬퍼 ──────────────────────────────────────────────────────────────────

def _to_out(s: SharedDocument) -> ShareOut:
    return ShareOut(
        token=s.token,
        title=s.title,
        file_type=s.file_type,
        expires_at=s.expires_at,
        max_downloads=s.max_downloads,
        download_count=s.download_count,
        has_password=bool(s.password_hash),
        revoked=bool(s.revoked),
        created_at=s.created_at,
    )


def _load_active(token: str, db: Session) -> SharedDocument:
    """살아 있는 공유만 돌려줍니다. 없는 토큰과 만료된 토큰을 구분하지 않습니다.

    구분해서 알려주면 토큰이 존재하는지를 확인하는 통로가 됩니다.
    """
    share = db.query(SharedDocument).filter(SharedDocument.token == token).first()

    if not share or share.revoked:
        raise HTTPException(status_code=404, detail="링크를 찾을 수 없습니다.")

    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="만료된 링크입니다.")

    if share.max_downloads is not None and share.download_count >= share.max_downloads:
        raise HTTPException(status_code=410, detail="다운로드 횟수를 모두 사용했습니다.")

    return share


def _remaining(share: SharedDocument) -> int | None:
    if share.max_downloads is None:
        return None
    return max(0, share.max_downloads - share.download_count)


# ── 만들기 · 관리 (로그인 필요) ───────────────────────────────────────────

@router.post("/", response_model=ShareOut)
def create_share(
    body: ShareCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(ConversionHistory)
        .filter(
            ConversionHistory.id == body.history_id,
            ConversionHistory.user_id == user.id,
        )
        .first()
    )
    if not history:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    expires_at = (
        datetime.utcnow() + timedelta(days=body.expires_in_days)
        if body.expires_in_days
        else None
    )

    share = SharedDocument(
        token=secrets.token_urlsafe(24),
        history_id=history.id,
        owner_id=user.id,
        title=history.title,
        file_type=history.file_type,
        file_url=history.file_url,
        expires_at=expires_at,
        max_downloads=body.max_downloads,
        password_hash=hash_password(body.password) if body.password else None,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return _to_out(share)


@router.get("/", response_model=list[ShareOut])
def list_shares(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내가 공유한 문서 목록 — 프런트의 '공유 문서' 탭이 씁니다."""
    rows = (
        db.query(SharedDocument)
        .filter(SharedDocument.owner_id == user.id)
        .order_by(SharedDocument.created_at.desc())
        .all()
    )
    return [_to_out(r) for r in rows]


@router.delete("/{token}")
def revoke_share(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """공유 해제. 행을 지우지 않고 revoked 로 두어 이력을 남깁니다."""
    share = (
        db.query(SharedDocument)
        .filter(SharedDocument.token == token, SharedDocument.owner_id == user.id)
        .first()
    )
    if not share:
        raise HTTPException(status_code=404, detail="링크를 찾을 수 없습니다.")

    share.revoked = True
    db.commit()
    return {"ok": True}


# ── 열람 (로그인 불필요) ──────────────────────────────────────────────────

@router.get("/public/{token}", response_model=SharedView)
def view_shared(token: str, db: Session = Depends(get_db)):
    """링크를 연 사람에게 보여줄 정보.

    비밀번호가 걸려 있으면 file_url 을 담지 않습니다. 여기서 주면
    비밀번호 입력을 건너뛰고 받을 수 있습니다.
    """
    share = _load_active(token, db)
    locked = bool(share.password_hash)
    return SharedView(
        title=share.title,
        file_type=share.file_type,
        expires_at=share.expires_at,
        requires_password=locked,
        remaining_downloads=_remaining(share),
        file_url=None if locked else share.file_url,
    )


@router.post("/public/{token}/access", response_model=SharedView)
def access_shared(token: str, body: AccessBody, db: Session = Depends(get_db)):
    """다운로드 직전에 부릅니다. 여기서만 횟수가 올라갑니다."""
    share = _load_active(token, db)

    if share.password_hash:
        if not body.password or not verify_password(body.password, share.password_hash):
            raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")

    share.download_count += 1
    db.commit()
    db.refresh(share)

    return SharedView(
        title=share.title,
        file_type=share.file_type,
        expires_at=share.expires_at,
        requires_password=bool(share.password_hash),
        remaining_downloads=_remaining(share),
        file_url=share.file_url,
    )
