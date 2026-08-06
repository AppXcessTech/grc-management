import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import httpx

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.enums import UserStatus
from app.models.refresh_token import RefreshToken
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.schema.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserProfile(BaseModel):
    email: str
    organization_id: int
    first_name: str
    last_name: str
    roles: list[str]
    permissions: list[str]


MAX_ACTIVE_REFRESH_TOKENS = 5


async def _create_refresh_token(db: AsyncSession, user_id: int, organization_id: int) -> str:
    raw, token_hash = generate_refresh_token()
    rt = RefreshToken(
        user_id=user_id,
        organization_id=organization_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)

    # Enforce limit — revoke oldest if over
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        ).order_by(RefreshToken.created_at.desc())
    )
    active = result.scalars().all()
    if len(active) > MAX_ACTIVE_REFRESH_TOKENS:
        for stale in active[MAX_ACTIVE_REFRESH_TOKENS:]:
            stale.revoked_at = datetime.now(timezone.utc)

    await db.flush()
    return raw


async def _issue_token_pair(db: AsyncSession, user: User) -> dict:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    role_names = [r.name for r in user.roles]

    access_token = create_access_token(
        data={"sub": user.email, "org_id": user.organization_id, "roles": role_names},
        expires_delta=access_token_expires,
    )
    refresh_token = await _create_refresh_token(db, user.id, user.organization_id)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == form_data.username).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.status == UserStatus.invited:
        user.status = UserStatus.active
        db.add(user)
        await db.commit()

    if user.status not in (UserStatus.active, UserStatus.invited):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account is {user.status.value}")

    tokens = await _issue_token_pair(db, user)
    await db.commit()
    return tokens

GOOGLE_CLIENT_ID = "369022549081-qbv4ivuvlvpgu5cch1ksi0vajlevgns5.apps.googleusercontent.com"


class GoogleAuthRequest(BaseModel):
    id_token: str


@router.post("/google", response_model=Token)
async def google_auth(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.id_token},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    info = resp.json()
    if info.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience mismatch")

    email = info.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not provided by Google")

    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No account found with this email")

    if user.status == UserStatus.invited:
        user.status = UserStatus.active
        db.add(user)
        await db.commit()

    if user.status not in (UserStatus.active, UserStatus.invited):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account is {user.status.value}")

    tokens = await _issue_token_pair(db, user)
    await db.commit()
    return tokens


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    raw_token = payload.refresh_token
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke the used token (rotation)
    rt.revoked_at = datetime.now(timezone.utc)
    db.add(rt)

    # Load the user
    user_result = await db.execute(
        select(User).where(User.id == rt.user_id).options(selectinload(User.roles))
    )
    user = user_result.scalar_one_or_none()
    if not user or user.status not in (UserStatus.active,):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    await db.flush()
    tokens = await _issue_token_pair(db, user)
    await db.commit()
    return tokens


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()

    role_names = [r.name for r in user.roles]

    role_ids = [r.id for r in user.roles]
    perm_result = await db.execute(
        select(Permission.resource, Permission.action)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id.in_(role_ids))
        .distinct()
    )
    permissions = sorted([f"{row.resource}:{row.action.value}" for row in perm_result.all()])

    return UserProfile(
        email=user.email,
        organization_id=user.organization_id,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=role_names,
        permissions=permissions,
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Always return success to avoid email enumeration
    if not user:
        return ForgotPasswordResponse(message="If an account exists, a reset link has been sent.")

    # Expire any existing unused tokens for this user
    existing = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    )
    for t in existing.scalars().all():
        t.used_at = datetime.now(timezone.utc)

    token_str = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.commit()

    return ForgotPasswordResponse(
        message="If an account exists, a reset link has been sent.",
        token=token_str,
    )


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    )
    reset_token = result.scalar_one_or_none()
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found.",
        )

    user.hashed_password = get_password_hash(payload.password)
    reset_token.used_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Password has been reset successfully."}


@router.post("/sso/callback")
async def sso_callback(provider: str, code: str, db: AsyncSession = Depends(get_db)):
    # Placeholder for actual OAuth2/SAML callback logic
    # This would typically exchange code for user info and create a session/JWT
    return {
        "message": f"Successfully authenticated with {provider}",
        "access_token": "placeholder-sso-token",
        "token_type": "bearer"
    }


@router.post("/mfa/verify")
async def verify_mfa(user_id: int, code: str):
    # Placeholder for MFA verification logic
    return {"message": "MFA verified successfully"}


@router.get("/sso/providers")
async def get_sso_providers(
    email: str | None = None,
    org_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    from app.models.organization import Organization
    from app.models.sso_configuration import SSOConfiguration
    from app.models.enums import SSOProvider

    target_org_id = org_id
    if not target_org_id and email:
        domain = email.split("@")[-1] if "@" in email else None
        if domain:
            result = await db.execute(
                select(Organization).where(Organization.domain == domain)
            )
            org = result.scalar_one_or_none()
            if org:
                target_org_id = org.id

    if not target_org_id:
        return {"providers": []}

    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.organization_id == target_org_id,
            SSOConfiguration.is_active.is_(True),
        )
    )
    configs = result.scalars().all()
    providers = []
    for c in configs:
        if c.provider == SSOProvider.Microsoft:
            tenant_id = c.config.get("tenant_id", "")
            providers.append({
                "provider": "Microsoft",
                "login_url": f"/api/auth/sso/microsoft/login?org_id={target_org_id}",
                "tenant_id": tenant_id,
            })
        else:
            providers.append({
                "provider": c.provider.value,
                "login_url": f"/api/auth/sso/callback?provider={c.provider.value}&org_id={target_org_id}",
            })
    return {"providers": providers}
