import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.audit_log import AuditLog
from app.models.endpoint_device import EndpointDevice
from app.models.user import User

router = APIRouter(prefix="/api/integrations/manageengine-mdm", tags=["integrations"])

OAUTH_TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"
MDM_API_URL = "https://mdm.manageengine.in/api/v1/mdm/devices"
CONFIG_DIR = Path("data/mdm_config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class SyncResult(BaseModel):
    total: int
    created: int
    updated: int
    errors: List[str] = []


class SetupRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str


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


async def get_refresh_token(org_id: int) -> str:
    config = _load_config(org_id)
    token = config.get("refresh_token", "").strip()
    if not token:
        token = os.environ.get("REFRESH_TOKEN", "").strip()
    return token


async def get_client_credentials(org_id: int) -> tuple[str, str]:
    config = _load_config(org_id)
    client_id = config.get("client_id", "").strip() or os.environ.get("CLIENT_ID", "").strip()
    client_secret = config.get("client_secret", "").strip() or os.environ.get("CLIENT_SECRET", "").strip()
    return client_id, client_secret


async def get_access_token(org_id: int) -> str:
    client_id, client_secret = await get_client_credentials(org_id)
    refresh_token = await get_refresh_token(org_id)

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="CLIENT_ID and CLIENT_SECRET must be configured")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="REFRESH_TOKEN not found. Run Setup first to authenticate with ManageEngine.")

    async with httpx.AsyncClient(timeout=60, verify=True) as client:
        resp = await client.post(OAUTH_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"]


DEVICE_TYPE_MAP = {
    "1": "Mobile Device",
    "2": "Tablet",
    "3": "Desktop Computer",
    "4": "iPhone",
    "5": "Android Phone",
    "9": "Windows Laptop",
    "10": "macOS Laptop",
    "11": "Linux Workstation",
}


@router.post("/setup", response_model=SetupResult)
async def setup_mdm_integration(body: SetupRequest, current_user: CurrentUserDep, db: DBSessionDep):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(OAUTH_TOKEN_URL, data={
            "code": body.code,
            "client_id": body.client_id,
            "client_secret": body.client_secret,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=f"OAuth error: {data['error']}")

        refresh_token = data["refresh_token"]

    _save_config(current_user.organization_id, {
        "client_id": body.client_id,
        "client_secret": body.client_secret,
        "refresh_token": refresh_token,
    })

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="mdm_setup",
        resource_type="integration",
        new_values={"refresh_token_obtained": True},
    ))
    await db.commit()

    return SetupResult(success=True, message="ManageEngine MDM setup complete. You can now sync devices.")


async def _find_device(db, org_id: int, device: dict):
    device_id = device.get("device_id", "")
    raw_serial = (device.get("serial_number") or "").strip()
    udid = device.get("udid", "")
    serial = raw_serial or udid or device_id

    stmt = select(EndpointDevice).where(EndpointDevice.organization_id == org_id)

    stmt = stmt.where(
        or_(
            EndpointDevice.mdm_device_id == device_id,
            EndpointDevice.serial_number == serial,
            EndpointDevice.serial_number == udid,
            EndpointDevice.serial_number == device_id,
        )
    )

    result = await db.execute(stmt.limit(1))
    return result.scalar_one_or_none()


def _parse_device_fields(device: dict) -> dict:
    user_info = device.get("user", {})
    owned_by = ""
    user_id = ""
    user_email = ""
    if user_info:
        owned_by = user_info.get("user_name", "") or user_info.get("user_email", "")
        user_id = user_info.get("user_id", "")
        user_email = user_info.get("user_email", "")

    product_name = device.get("product_name", "")
    manufacturer = "Samsung" if product_name and "SM-" in product_name else ""

    raw_serial = (device.get("serial_number") or "").strip()
    udid = device.get("udid", "")
    device_id = device.get("device_id", "")
    serial_number = raw_serial or udid or device_id

    return {
        "device_id": device_id,
        "device_name": device.get("device_name", ""),
        "platform_type": device.get("platform_type", ""),
        "os_version": device.get("os_version", ""),
        "model": device.get("model", ""),
        "product_name": product_name,
        "serial_number": serial_number,
        "udid": udid,
        "owned_by": owned_by,
        "user_id": user_id,
        "user_email": user_email,
        "customer_id": device.get("customer_id", ""),
        "managed_status": device.get("managed_status", ""),
        "is_supervised": device.get("is_supervised", False),
        "is_removed": device.get("is_removed", "false"),
        "last_contact_time": device.get("last_contact_time", ""),
        "asset_type": DEVICE_TYPE_MAP.get(str(device.get("device_type", "")), "Mobile Device"),
        "manufacturer": manufacturer,
    }


@router.post("/sync", response_model=SyncResult)
async def sync_mdm_devices(current_user: CurrentUserDep, db: DBSessionDep):
    result = SyncResult(total=0, created=0, updated=0, errors=[])

    try:
        access_token = await get_access_token(current_user.organization_id)
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Cannot reach Zoho OAuth: {str(e)}")

    headers = {"Authorization": f"Zoho-oauthtoken {access_token}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(MDM_API_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            devices = data.get("devices", [])
            if isinstance(devices, dict):
                devices = [devices]

            result.total = len(devices)

            for device in devices:
                try:
                    fields = _parse_device_fields(device)
                    mdm_payload = json.dumps(fields)

                    assigned_to = None
                    if fields["user_email"]:
                        user_result = await db.execute(
                            select(User).where(User.email == fields["user_email"])
                        )
                        matched_user = user_result.scalar_one_or_none()
                        if matched_user:
                            assigned_to = matched_user.id
                        else:
                            fname, _, lname = fields["owned_by"].partition(" ")
                            new_user = User(
                                organization_id=current_user.organization_id,
                                email=fields["user_email"],
                                first_name=fname or "MDM",
                                last_name=lname or "User",
                                status="active",
                            )
                            db.add(new_user)
                            await db.flush()
                            assigned_to = new_user.id

                    existing = await _find_device(db, current_user.organization_id, device)
                    now = datetime.now(timezone.utc)

                    if existing:
                        existing.name = fields["device_name"]
                        existing.manufacturer = fields["manufacturer"]
                        existing.model = fields["model"]
                        existing.serial_number = fields["serial_number"]
                        existing.mdm_device_id = fields["device_id"]
                        existing.mdm_payload = mdm_payload
                        existing.assigned_to = assigned_to
                        existing.updated_at = now
                        result.updated += 1
                    else:
                        db.add(EndpointDevice(
                            organization_id=current_user.organization_id,
                            name=fields["device_name"],
                            asset_type=fields["asset_type"],
                            status="Active",
                            manufacturer=fields["manufacturer"],
                            model=fields["model"],
                            serial_number=fields["serial_number"],
                            mdm_device_id=fields["device_id"],
                            mdm_payload=mdm_payload,
                            assigned_to=assigned_to,
                            created_by=current_user.id,
                        ))
                        result.created += 1

                except Exception as e:
                    result.errors.append(f"Device '{device.get('device_name', 'unknown')}': {str(e)}")

            await db.flush()

            device_ids = [d.get("device_id") for d in devices if d.get("device_id")]
            if device_ids:
                async def _fetch_registered_time(did: str) -> tuple[str, datetime | None]:
                    try:
                        detail_resp = await client.get(f"{MDM_API_URL}/{did}", headers=headers)
                        detail_resp.raise_for_status()
                        detail_data = detail_resp.json()
                        rt = detail_data.get("registered_time", "")
                        if rt:
                            epoch_ms = int(rt)
                            return did, datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
                    except Exception:
                        pass
                    return did, None

                import asyncio
                results = await asyncio.gather(*[_fetch_registered_time(did) for did in device_ids])

                for did, reg_date in results:
                    if reg_date:
                        dev_result = await db.execute(
                            select(EndpointDevice).where(
                                EndpointDevice.organization_id == current_user.organization_id,
                                EndpointDevice.mdm_device_id == did,
                            )
                        )
                        dev = dev_result.scalar_one_or_none()
                        if dev:
                            dev.acquisition_date = reg_date

            db.add(AuditLog(
                organization_id=current_user.organization_id,
                user_id=current_user.id,
                action="mdm_sync",
                resource_type="endpoint_device",
                new_values={"total": result.total, "created": result.created, "updated": result.updated, "errors": len(result.errors)},
            ))
            await db.commit()

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"ManageEngine API error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Cannot reach ManageEngine MDM: {str(e)}")

    return result


class DeviceDetailResult(BaseModel):
    device_name: str = ""
    manufacturer: str = ""
    model: str = ""
    os_version: str = ""
    platform_type: str = ""
    serial_number: str = ""
    udid: str = ""
    device_id: str = ""
    owned_by: str = ""
    user_id: str = ""
    is_supervised: bool = False
    is_removed: str = "false"
    last_contact_time: str = ""
    battery_level: str = ""
    registered_time: str = ""
    added_time: str = ""
    raw: dict = {}


@router.get("/devices/{device_id}", response_model=DeviceDetailResult)
async def mdm_device_details(device_id: str, current_user: CurrentUserDep, db: DBSessionDep):
    access_token = await get_access_token(current_user.organization_id)
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{MDM_API_URL}/{device_id}", headers=headers)
        resp.raise_for_status()
        data = resp.json()

    user_info = data.get("user", {})
    return DeviceDetailResult(
        device_name=data.get("device_name", ""),
        manufacturer=data.get("manufacturer", ""),
        model=data.get("model", ""),
        os_version=data.get("os_version", ""),
        platform_type=str(data.get("platform_type", "")),
        serial_number=(data.get("serial_number") or "").strip(),
        udid=data.get("udid", ""),
        device_id=data.get("device_id", ""),
        owned_by=user_info.get("user_name", "") or user_info.get("user_email", ""),
        user_id=user_info.get("user_id", ""),
        is_supervised=data.get("is_supervised", False),
        is_removed=data.get("is_removed", "false"),
        last_contact_time=data.get("last_contact_time", ""),
        battery_level=data.get("battery_level", ""),
        registered_time=data.get("registered_time", ""),
        added_time=data.get("added_time", ""),
        raw=data,
    )


class UserDevicesResult(BaseModel):
    email: str
    device_ids: List[str] = []


@router.get("/users/devices", response_model=UserDevicesResult)
async def mdm_user_devices(email: str, current_user: CurrentUserDep):
    access_token = await get_access_token(current_user.organization_id)
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://mdm.manageengine.in/api/v1/mdm/users/devices",
            headers=headers,
            params={"email_id": email},
        )
        resp.raise_for_status()
        data = resp.json()

    return UserDevicesResult(email=email, device_ids=data.get("device_ids", []))


class UpdateLifecycleResult(BaseModel):
    success: bool
    acquisition_date: str = ""
    message: str = ""


@router.post("/devices/{device_id}/update-lifecycle", response_model=UpdateLifecycleResult)
async def mdm_update_lifecycle(device_id: str, current_user: CurrentUserDep, db: DBSessionDep):
    access_token = await get_access_token(current_user.organization_id)
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{MDM_API_URL}/{device_id}", headers=headers)
        resp.raise_for_status()
        data = resp.json()

    registered_time = data.get("registered_time", "")
    if not registered_time:
        raise HTTPException(status_code=400, detail="No registered_time in MDM response")

    try:
        epoch_ms = int(registered_time)
        acquisition_date = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail=f"Invalid registered_time: {registered_time}")

    existing = await db.execute(
        select(EndpointDevice).where(
            EndpointDevice.organization_id == current_user.organization_id,
            EndpointDevice.mdm_device_id == device_id,
        )
    )
    device = existing.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in local database")

    device.acquisition_date = acquisition_date
    await db.commit()

    return UpdateLifecycleResult(
        success=True,
        acquisition_date=acquisition_date.isoformat(),
        message=f"Acquisition date set to {acquisition_date.date()} (registered_time from MDM)",
    )
