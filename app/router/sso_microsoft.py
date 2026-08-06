import json
import logging
import os
import secrets
import urllib.parse
from datetime import datetime, timezone

import httpx
import jwt
from jwt import PyJWK
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, DBSessionDep
from app.core.settings import settings
from app.models.enums import SSOProvider, UserStatus
from app.models.sso_configuration import SSOConfiguration
from app.models.user import User
from app.router.auth import _issue_token_pair

router = APIRouter(prefix="/api/auth/sso/microsoft", tags=["sso-microsoft"])

MICROSOFT_OAUTH_SCOPES = "openid email profile"
STATE_DIR = "/tmp/microsoft_state"

logger = logging.getLogger("sso.microsoft")


class MicrosoftConfigRequest(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str


def _redirect_error(params: str) -> RedirectResponse:
    """Redirect back to the frontend with an error query string."""
    return RedirectResponse(
        url=f"{settings.frontend_url.rstrip('/')}/login?{params}",
        status_code=302,
    )


@router.post("/configure", status_code=status.HTTP_200_OK)
async def configure_microsoft(
    payload: MicrosoftConfigRequest,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.organization_id == current_user.organization_id,
            SSOConfiguration.provider == SSOProvider.Microsoft,
        )
    )
    existing = result.scalar_one_or_none()

    config_data = {
        "tenant_id": payload.tenant_id,
        "client_secret": payload.client_secret,
    }

    if existing:
        existing.client_id = payload.client_id
        existing.config = config_data
        existing.is_active = True
    else:
        sso = SSOConfiguration(
            organization_id=current_user.organization_id,
            provider=SSOProvider.Microsoft,
            client_id=payload.client_id,
            config=config_data,
            is_active=True,
        )
        db.add(sso)

    await db.commit()
    return {"message": "Microsoft Entra ID SSO configured successfully"}


@router.get("/config")
async def get_microsoft_config(
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.organization_id == current_user.organization_id,
            SSOConfiguration.provider == SSOProvider.Microsoft,
        )
    )
    sso = result.scalar_one_or_none()
    if not sso:
        return None
    return {
        "client_id": sso.client_id,
        "tenant_id": sso.config.get("tenant_id", ""),
        "is_active": sso.is_active,
    }


@router.get("/login")
async def microsoft_login(
    org_id: int = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.organization_id == org_id,
            SSOConfiguration.provider == SSOProvider.Microsoft,
            SSOConfiguration.is_active.is_(True),
        )
    )
    sso = result.scalar_one_or_none()
    if not sso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Microsoft SSO not configured for this organization",
        )

    tenant_id = sso.config.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not configured",
        )

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(16)
    callback_url = f"{settings.backend_url.rstrip('/')}/api/auth/sso/microsoft/callback"

    os.makedirs(STATE_DIR, exist_ok=True)
    with open(os.path.join(STATE_DIR, f"{state}.json"), "w") as f:
        json.dump({"nonce": nonce, "org_id": org_id, "tenant_id": tenant_id}, f)

    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    params = {
        "client_id": sso.client_id,
        "response_type": "code",
        "response_mode": "query",
        "scope": MICROSOFT_OAUTH_SCOPES,
        "redirect_uri": callback_url,
        "prompt": "select_account",
        "state": state,
        "nonce": nonce,
    }
    redirect_url = f"{auth_url}?{urllib.parse.urlencode(params)}"

    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/callback")
async def microsoft_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return _redirect_error(f"error={urllib.parse.quote(error)}")

    if not code or not state:
        return _redirect_error("error=missing_params")

    state_path = f"{STATE_DIR}/{state}.json"
    if not os.path.exists(state_path):
        return _redirect_error("error=invalid_state")
    with open(state_path) as f:
        state_data = json.load(f)
    os.remove(state_path)

    org_id = state_data["org_id"]
    tenant_id = state_data["tenant_id"]
    expected_nonce = state_data["nonce"]

    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.organization_id == org_id,
            SSOConfiguration.provider == SSOProvider.Microsoft,
        )
    )
    sso = result.scalar_one_or_none()
    if not sso:
        return _redirect_error("error=config_not_found")

    callback_url = f"{settings.backend_url.rstrip('/')}/api/auth/sso/microsoft/callback"
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url,
                "client_id": sso.client_id,
                "client_secret": sso.config.get("client_secret", ""),
            },
            headers={"Accept": "application/json"},
        )

    if token_resp.status_code != 200:
        logger.error("Microsoft token exchange failed: %s", token_resp.text)
        return _redirect_error("error=token_exchange_failed")

    token_data = token_resp.json()
    id_token = token_data.get("id_token")
    if not id_token:
        return _redirect_error("error=no_id_token")

    try:
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        async with httpx.AsyncClient() as client:
            jwks_resp = await client.get(jwks_url)
        jwks = jwks_resp.json()

        header = jwt.get_unverified_header(id_token)
        key_data = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")),
            None,
        )
        if not key_data:
            return _redirect_error("error=no_verifying_key")

        claims = jwt.decode(
            id_token,
            PyJWK(key_data).key,
            algorithms=["RS256"],
            audience=sso.client_id,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        )

        # Verify the nonce we embedded in the authorize request to prevent
        # token replay / CSRF against the callback.
        if claims.get("nonce") != expected_nonce:
            return _redirect_error("error=nonce_mismatch")
    except Exception as e:
        logger.exception("Microsoft SSO token verification failed")
        return _redirect_error(
            f"error=invalid_token&detail={urllib.parse.quote(str(e))}"
        )

    # Entra ID (Azure AD) v2.0 tokens often omit the `email` claim (guests,
    # users without an Exchange mailbox, etc.). `preferred_username` is always
    # present and carries the sign-in UPN (user@domain).
    email = claims.get("email") or claims.get("preferred_username")
    if not email:
        return _redirect_error("error=no_email")

    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()

    if not user:
        return _redirect_error("error=no_account")

    if user.status == UserStatus.invited:
        user.status = UserStatus.active

    if user.status not in (UserStatus.active, UserStatus.invited):
        return _redirect_error("error=account_inactive")

    # Bind the SSO identity to the account so the flow is consistent on
    # subsequent logins and the SSO provider is visible in user profiles.
    oid = claims.get("oid")
    if user.sso_provider != SSOProvider.Microsoft or user.external_subject_id != oid:
        user.sso_provider = SSOProvider.Microsoft
        user.external_subject_id = oid
    user.last_login_at = datetime.now(timezone.utc)

    tokens = await _issue_token_pair(db, user)
    await db.commit()

    return RedirectResponse(
        url=(
            f"{settings.frontend_url.rstrip('/')}/login"
            f"?token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
        ),
        status_code=302,
    )
