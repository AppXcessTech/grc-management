import secrets
import urllib.parse
from datetime import timedelta

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
from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from app.models.enums import SSOProvider, UserStatus
from app.models.sso_configuration import SSOConfiguration
from app.models.user import User

router = APIRouter(prefix="/api/auth/sso/microsoft", tags=["sso-microsoft"])

MICROSOFT_OAUTH_SCOPES = "openid email profile"
FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://localhost:8000"


class MicrosoftConfigRequest(BaseModel):
    tenant_id: str
    client_id: str
    client_secret: str


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
            SSOConfiguration.is_active == True,
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
    callback_url = f"{BACKEND_URL}/api/auth/sso/microsoft/callback"
    backend_callback = f"{BACKEND_URL}/api/auth/sso/microsoft/callback"

    import json, os
    state_dir = "/tmp/microsoft_state"
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, f"{state}.json"), "w") as f:
        json.dump({"nonce": nonce, "org_id": org_id, "tenant_id": tenant_id}, f)

    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    params = {
        "client_id": sso.client_id,
        "response_type": "code",
        "response_mode": "query",
        "scope": MICROSOFT_OAUTH_SCOPES,
        "redirect_uri": backend_callback,
        "prompt": "select_account",
        "state": state,
        "nonce": nonce,
    }
    redirect_url = f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

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
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error={error}",
            status_code=302,
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=missing_params",
            status_code=302,
        )

    import json, os
    state_path = f"/tmp/microsoft_state/{state}.json"
    if not os.path.exists(state_path):
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=invalid_state",
            status_code=302,
        )
    with open(state_path) as f:
        state_data = json.load(f)
    os.remove(state_path)

    org_id = state_data["org_id"]
    tenant_id = state_data["tenant_id"]

    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.organization_id == org_id,
            SSOConfiguration.provider == SSOProvider.Microsoft,
        )
    )
    sso = result.scalar_one_or_none()
    if not sso:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=config_not_found",
            status_code=302,
        )

    callback_url = f"{BACKEND_URL}/api/auth/sso/microsoft/callback"
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
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=token_exchange_failed",
            status_code=302,
        )

    token_data = token_resp.json()
    id_token = token_data.get("id_token")
    if not id_token:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=no_id_token",
            status_code=302,
        )

    try:
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        async with httpx.AsyncClient() as client:
            jwks_resp = await client.get(jwks_url)
        jwks = jwks_resp.json()

        header = jwt.get_unverified_header(id_token)
        key_data = None
        for key in jwks.get("keys", []):
            if key.get("kid") == header.get("kid"):
                key_data = key
                break

        if not key_data:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=no_verifying_key",
                status_code=302,
            )

        claims = jwt.decode(
            id_token,
            PyJWK(key_data).key,
            algorithms=["RS256"],
            audience=sso.client_id,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        )
    except Exception as e:
        import logging
        logging.error(f"Microsoft SSO token verification failed: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=invalid_token&detail={urllib.parse.quote(str(e))}",
            status_code=302,
        )

    email = claims.get("email")
    if not email:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=no_email",
            status_code=302,
        )

    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()

    if not user:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=no_account",
            status_code=302,
        )

    if user.status == UserStatus.invited:
        user.status = UserStatus.active
        db.add(user)
        await db.commit()

    if user.status not in (UserStatus.active, UserStatus.invited):
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=account_inactive",
            status_code=302,
        )

    role_names = [r.name for r in user.roles]
    access_token = create_access_token(
        data={"sub": user.email, "org_id": user.organization_id, "roles": role_names},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return RedirectResponse(
        url=f"{FRONTEND_URL}/login?token={access_token}",
        status_code=302,
    )
