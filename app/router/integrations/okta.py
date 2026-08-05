import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.audit_log import AuditLog
from app.models.people_asset import PeopleAsset

router = APIRouter(prefix="/api/integrations/okta", tags=["integrations"])

CONFIG_DIR = Path("data/okta_config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class SyncResult(BaseModel):
    total: int
    created: int
    updated: int
    errors: List[str] = []


class SetupRequest(BaseModel):
    okta_domain: str
    okta_token: str


class SetupResult(BaseModel):
    success: bool
    message: str = ""


def _config_path(org_id: int) -> Path:
    return CONFIG_DIR / f"org_{org_id}.json"


def _load_config(org_id: int) -> dict:
    path = _config_path(org_id)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_config(org_id: int, data: dict):
    _config_path(org_id).write_text(json.dumps(data, indent=2))


def _get_okta_credentials(org_id: int) -> tuple[str, str]:
    config = _load_config(org_id)
    domain = config.get("okta_domain", "").strip() or os.environ.get("OKTA_DOMAIN", "").strip()
    token = config.get("okta_token", "").strip() or os.environ.get("OKTA_TOKEN", "").strip()
    return domain, token


@router.post("/setup", response_model=SetupResult)
async def setup_okta_integration(body: SetupRequest, current_user: CurrentUserDep, db: DBSessionDep):
    domain = body.okta_domain.strip().removeprefix("https://").removeprefix("http://").split("/")[0]

    if not domain or not body.okta_token.strip():
        raise HTTPException(status_code=400, detail="OKTA_DOMAIN and OKTA_TOKEN are required")

    _save_config(current_user.organization_id, {
        "okta_domain": domain,
        "okta_token": body.okta_token.strip(),
    })

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="okta_setup",
        resource_type="integration",
        new_values={"okta_domain_configured": True},
    ))
    await db.commit()

    return SetupResult(success=True, message="Okta integration configured. You can now sync users.")


@router.post("/sync")
async def sync_okta_users(current_user: CurrentUserDep, db: DBSessionDep):
    okta_domain, okta_token = _get_okta_credentials(current_user.organization_id)

    okta_domain = okta_domain.removeprefix("https://").removeprefix("http://").split("/")[0]

    if not okta_domain or not okta_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Okta not configured. Go to Settings → Configure to enter your OKTA_DOMAIN and OKTA_TOKEN.",
        )

    users_url = f"https://{okta_domain}/api/v1/users?limit=200"
    headers = {
        "Authorization": f"SSWS {okta_token}",
        "Accept": "application/json",
    }

    synced_at = datetime.now(timezone.utc).isoformat()

    result = SyncResult(total=0, created=0, updated=0, errors=[])

    existing_result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    existing_assets = existing_result.scalars().all()
    okta_id_to_asset: dict[str, PeopleAsset] = {}
    for asset in existing_assets:
        try:
            desc = json.loads(asset.description) if asset.description else {}
            okta_id = desc.get("oktaUserId", "")
            if okta_id:
                okta_id_to_asset[okta_id] = asset
        except (json.JSONDecodeError, TypeError):
            pass

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(users_url, headers=headers)
            resp.raise_for_status()
            okta_users = resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Okta API error ({users_url}): {e.response.status_code} - {e.response.text[:300]}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to reach Okta at {users_url}: {repr(e)}",
            )

        result.total = len(okta_users)

        for okta_user in okta_users:
            try:
                profile = okta_user.get("profile", {})
                user_id = okta_user.get("id", "")
                email = profile.get("email", "")
                if not email:
                    continue

                first_name = profile.get("firstName", "")
                last_name = profile.get("lastName", "")
                name = f"{first_name} {last_name}".strip()
                if not name:
                    continue

                employee_number = profile.get("employeeNumber") or ""
                department = profile.get("department") or ""
                title = profile.get("title") or ""
                manager_name = profile.get("manager") or ""
                location = profile.get("location") or ""
                employment_type = profile.get("employmentType") or profile.get("employeeType") or ""
                start_date_attr = profile.get("startDate") or ""
                termination_date = profile.get("terminationDate") or ""
                okta_status = okta_user.get("status", "ACTIVE")

                status_map = {
                    "ACTIVE": "Active",
                    "SUSPENDED": "Suspended",
                    "DEPROVISIONED": "Offboarding",
                    "LOCKED_OUT": "Suspended",
                    "PASSWORD_EXPIRED": "Active",
                    "PROVISIONED": "Active",
                    "RECOVERY": "Active",
                    "STAGED": "Active",
                }
                mapped_status = status_map.get(okta_status, "Active")

                okta_created = okta_user.get("created", "")
                start_date = None
                if okta_created:
                    try:
                        start_date = datetime.fromisoformat(okta_created.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        start_date = None

                last_login_str = okta_user.get("lastLogin") or ""
                last_password_change = okta_user.get("passwordChanged") or ""

                mfa_enabled = False
                mfa_method = "None"
                if user_id:
                    try:
                        factors_resp = await client.get(
                            f"https://{okta_domain}/api/v1/users/{user_id}/factors",
                            headers=headers,
                        )
                        if factors_resp.status_code == 200:
                            factors = factors_resp.json()
                            active_factors = [f for f in factors if f.get("status") == "ACTIVE"]
                            if active_factors:
                                mfa_enabled = True
                                factor_type = active_factors[0].get("factorType", "")
                                provider = active_factors[0].get("provider", "")
                                if factor_type == "webauthn":
                                    mfa_method = "FIDO2"
                                elif factor_type == "token:software:totp":
                                    mfa_method = "TOTP"
                                elif factor_type == "sms":
                                    mfa_method = "SMS"
                                elif factor_type == "push":
                                    mfa_method = "Push"
                                elif factor_type == "email":
                                    mfa_method = "Email OTP"
                                elif factor_type == "question":
                                    mfa_method = "Security Question"
                                else:
                                    mfa_method = "TOTP"
                    except Exception:
                        pass

                groups = okta_user.get("groups", [])
                privileged = okta_user.get("privileged_user", False)

                description = {
                    "oktaUserId": user_id,
                    "identityProvider": "Okta",
                    "syncedAt": synced_at,
                    "employeeId": employee_number,
                    "employmentType": employment_type,
                    "jobTitle": title,
                    "authMethod": "SSO + MFA" if mfa_enabled else "SSO",
                    "workArrangement": "On-site",
                    "location": location,
                    "mfa": {
                        "enrolled": mfa_enabled,
                        "enforced": mfa_enabled,
                        "method": mfa_method,
                        "enrollmentDate": "",
                        "lastVerifiedDate": "",
                        "verificationSource": "Okta",
                        "exceptionGranted": False,
                        "exceptionReason": "",
                        "exceptionApprovedBy": "",
                        "exceptionExpiryDate": "",
                        "evidence": [],
                        "notes": f"Synced from Okta on {synced_at}",
                    },
                    "backgroundCheck": "Not Required",
                    "ndaSigned": False,
                    "lastPasswordChange": last_password_change,
                    "complianceTraining": {
                        "securityAwareness": "N/A",
                        "gdpr": "N/A",
                        "aup": "N/A",
                        "codeOfConduct": "N/A",
                        "phishing": "N/A",
                    },
                    "joinDate": "",
                    "startDate": start_date_attr,
                    "terminationDate": termination_date,
                    "transferDate": "",
                    "exitDate": "",
                    "offboardingStatus": "N/A",
                    "roles": [],
                    "groups": groups,
                    "privilegedAccess": privileged,
                    "vpnAccess": False,
                    "pamVault": False,
                    "lastLogin": last_login_str,
                    "lastAccessReview": "",
                    "assetOwner": "",
                    "reviewer": "",
                    "reviewFrequency": "Quarterly",
                    "evidenceAttachments": [],
                    "exceptions": [],
                    "findings": [],
                }

                existing_asset = okta_id_to_asset.get(user_id)
                if existing_asset:
                    existing_asset.name = name
                    existing_asset.email = email
                    existing_asset.department = department if department else None
                    existing_asset.job_title = title if title else None
                    existing_asset.manager = manager_name if manager_name else None
                    existing_asset.status = mapped_status
                    existing_asset.start_date = start_date
                    existing_asset.description = json.dumps(description)
                    existing_asset.updated_at = datetime.now(timezone.utc)

                    db.add(AuditLog(
                        organization_id=current_user.organization_id,
                        user_id=current_user.id,
                        action="updated",
                        resource_type="people_asset",
                        resource_id=str(existing_asset.id),
                        new_values={"name": name, "email": email, "source": "okta_sync"},
                    ))

                    result.updated += 1
                else:
                    asset = PeopleAsset(
                        organization_id=current_user.organization_id,
                        created_by=current_user.id,
                        name=name,
                        email=email,
                        asset_type="Employee",
                        department=department if department else None,
                        job_title=title if title else None,
                        manager=manager_name if manager_name else None,
                        status=mapped_status,
                        start_date=start_date,
                        end_date=None,
                        description=json.dumps(description),
                    )
                    db.add(asset)
                    await db.flush()

                    db.add(AuditLog(
                        organization_id=current_user.organization_id,
                        user_id=current_user.id,
                        action="created",
                        resource_type="people_asset",
                        resource_id=str(asset.id),
                        new_values={"name": name, "email": email, "source": "okta_sync"},
                    ))

                    result.created += 1

            except Exception as e:
                result.errors.append(f"{okta_user.get('profile', {}).get('email', 'unknown')}: {str(e)}")

    await db.commit()
    return result
