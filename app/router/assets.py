from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep, CurrentBulkImportDep, DBSessionDep
from app.models.asset import Asset
from app.models.asset_tag import AssetTag
from app.models.asset_owner import AssetOwner
from app.models.asset_import_request import AssetImportRequest
from app.models.asset_suggestion import AssetSuggestion
from app.models.asset_category import AssetCategory
from app.models.user import User
from app.schema.asset import AssetCreate, AssetRead, AssetUpdate
from app.schema.asset_import_request import AssetImportRequestCreate, AssetImportRequestRead, AssetImportRequestReview
from app.schema.asset_suggestion import AssetSuggestionCreate, AssetSuggestionRead, AssetSuggestionReview
from app.services.steampipe_aws import validate_connection, import_aws_resources_via_steampipe
from app.services.ingestion import IngestionService
from app.services.notifications import notify_admins


# Column name mapping: DB column -> Pydantic field for encrypted columns
_ENCRYPTED_FIELD_MAP = {
    "role_arn_encrypted": "role_arn",
    "region_encrypted": "region",
    "account_name_encrypted": "account_name",
}


def _import_request_to_dict(req: AssetImportRequest) -> dict:
    """Convert AssetImportRequest to dict using property accessors for encrypted fields."""
    data = {}
    for c in req.__table__.columns:
        field_name = _ENCRYPTED_FIELD_MAP.get(c.name, c.name)
        data[field_name] = getattr(req, field_name)  # Uses @property which decrypts
    return data

router = APIRouter(prefix="/api/assets", tags=["assets"])


class AWSImportRequest(BaseModel):
    role_arn: str
    account_name: Optional[str] = None
    external_id: Optional[str] = None
    region: str = "us-east-1"


class AWSImportResponse(BaseModel):
    status: str
    message: str
    resources_discovered: int
    assets_stored: int
    relationships_created: int


@router.post("/", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset(payload: AssetCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Asset:
    tags_data = payload.tags or []
    create_data = payload.model_dump(exclude={"tags"})
    asset = Asset(organization_id=current_user.organization_id, **create_data)
    db.add(asset)
    await db.flush()

    for tag in tags_data:
        db.add(AssetTag(asset_id=asset.id, key=tag.get("key", ""), value=tag.get("value")))

    if payload.owner_id:
        db.add(AssetOwner(asset_id=asset.id, user_id=payload.owner_id))

    await db.commit()
    result = await db.execute(
        select(Asset)
        .where(Asset.id == asset.id)
        .options(selectinload(Asset.category), selectinload(Asset.tags), selectinload(Asset.owner))
    )
    return result.scalar_one()


@router.get("/", response_model=List[AssetRead])
async def list_assets(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    criticality: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> List[Asset]:
    query = (
        select(Asset)
        .where(Asset.organization_id == current_user.organization_id)
        .options(selectinload(Asset.category), selectinload(Asset.tags), selectinload(Asset.owner))
    )

    if search:
        query = query.where(Asset.name.ilike(f"%{search}%"))
    if category_id:
        query = query.where(Asset.category_id == category_id)
    if criticality:
        query = query.where(Asset.criticality.ilike(criticality))
    if risk_level:
        query = query.where(Asset.risk_level.ilike(risk_level))
    if source:
        query = query.where(Asset.source.ilike(source))
    if status:
        query = query.where(Asset.status.ilike(status))

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(asset_id: int, current_user: CurrentUserDep, db: DBSessionDep) -> Asset:
    result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_id, Asset.organization_id == current_user.organization_id)
        .options(selectinload(Asset.category), selectinload(Asset.tags), selectinload(Asset.owner))
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetRead)
async def update_asset(asset_id: int, payload: AssetUpdate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Asset:
    result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_id, Asset.organization_id == current_user.organization_id)
        .options(selectinload(Asset.category), selectinload(Asset.tags), selectinload(Asset.owner))
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    update_data = payload.model_dump(exclude_unset=True, exclude={"tags"})
    for field, value in update_data.items():
        setattr(asset, field, value)

    if payload.tags is not None:
        await db.execute(
            AssetTag.__table__.delete().where(AssetTag.asset_id == asset_id)
        )
        for tag in payload.tags:
            db.add(AssetTag(asset_id=asset_id, key=tag.get("key", ""), value=tag.get("value")))

    await db.commit()
    await db.refresh(asset)
    return asset


@router.put("/{asset_id}", response_model=AssetRead)
async def replace_asset(asset_id: int, payload: AssetUpdate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Asset:
    result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_id, Asset.organization_id == current_user.organization_id)
        .options(selectinload(Asset.category), selectinload(Asset.tags), selectinload(Asset.owner))
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    update_data = payload.model_dump(exclude_unset=True, exclude={"tags"})
    for field, value in update_data.items():
        setattr(asset, field, value)

    if payload.tags is not None:
        await db.execute(
            AssetTag.__table__.delete().where(AssetTag.asset_id == asset_id)
        )
        for tag in payload.tags:
            db.add(AssetTag(asset_id=asset_id, key=tag.get("key", ""), value=tag.get("value")))

    await db.commit()
    await db.refresh(asset)
    return asset


@router.post("/validate-aws")
async def validate_aws(payload: AWSImportRequest, current_user: CurrentBulkImportDep):
    conn = validate_connection(payload.role_arn, payload.external_id, payload.region)
    if not conn["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AWS connection failed: {conn.get('error', 'Unknown error')}",
        )
    return {"status": "success", "account_id": conn["account_id"]}


@router.post("/import-aws", response_model=AWSImportResponse)
async def import_aws(payload: AWSImportRequest, current_user: CurrentBulkImportDep, db: DBSessionDep):
    conn = validate_connection(payload.role_arn, payload.external_id, payload.region)
    if not conn["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AWS connection failed: {conn.get('error', 'Unknown error')}",
        )

    try:
        result = await import_aws_resources_via_steampipe(
            payload.role_arn,
            payload.account_name,
            payload.external_id,
            payload.region,
            db,
        )

        svc = IngestionService()
        ingest_result = await svc.ingest_from_result(
            current_user.organization_id,
            result,
            payload.region,
            result.get("account_id"),
        )

        # Only commit after ALL steps (discovery + ingestion) succeed.
        # If the network cuts mid-import, the session rolls back and no
        # partial data (e.g. raw API responses without assets) is stored.
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )

    return AWSImportResponse(
        status="success",
        message=f"Import complete: {result['resources_discovered']} resources discovered",
        resources_discovered=result["resources_discovered"],
        assets_stored=ingest_result["assets_stored"],
        relationships_created=ingest_result["relationships_created"],
    )


@router.post("/import-requests", response_model=AssetImportRequestRead, status_code=status.HTTP_201_CREATED)
async def create_import_request(payload: AssetImportRequestCreate, current_user: CurrentUserDep, db: DBSessionDep):
    req = AssetImportRequest(
        organization_id=current_user.organization_id,
        requested_by_id=current_user.id,
        role_arn=payload.role_arn,
        account_name=payload.account_name,
        region=payload.region,
        status="pending",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    user_result = await db.execute(select(User).where(User.id == req.requested_by_id))
    user = user_result.scalar_one_or_none()
    submitter_name = f"{user.first_name} {user.last_name}".strip() or user.email if user else "A user"

    await notify_admins(
        db,
        current_user.organization_id,
        "New AWS Import Request",
        f"{submitter_name} requested an AWS import ({req.role_arn})",
        notification_type="import_request",
        reference_type="import_request",
        reference_id=req.id,
    )
    await db.commit()

    return AssetImportRequestRead(
        **_import_request_to_dict(req),
        requested_by_name=submitter_name,
        reviewed_by_name=None,
    )


@router.get("/import-requests", response_model=List[AssetImportRequestRead])
async def list_import_requests(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    is_admin = any(role.name in ("super_admin", "compliance_admin") for role in current_user.roles)

    query = select(AssetImportRequest).where(AssetImportRequest.organization_id == current_user.organization_id)
    if not is_admin:
        query = query.where(AssetImportRequest.requested_by_id == current_user.id)
    if status_filter:
        query = query.where(AssetImportRequest.status == status_filter)
    query = query.order_by(AssetImportRequest.created_at.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    user_ids = {r.requested_by_id for r in requests} | {r.reviewed_by_id for r in requests if r.reviewed_by_id}
    users = {}
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: f"{u.first_name} {u.last_name}".strip() or u.email for u in user_result.scalars().all()}

    return [
        AssetImportRequestRead(
            **_import_request_to_dict(r),
            requested_by_name=users.get(r.requested_by_id),
            reviewed_by_name=users.get(r.reviewed_by_id) if r.reviewed_by_id else None,
        )
        for r in requests
    ]


@router.get("/import-requests/{request_id}", response_model=AssetImportRequestRead)
async def get_import_request(request_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(AssetImportRequest).where(
            AssetImportRequest.id == request_id,
            AssetImportRequest.organization_id == current_user.organization_id,
        )
    )
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import request not found")

    user_result = await db.execute(select(User).where(User.id == req.requested_by_id))
    requested_by = user_result.scalar_one_or_none()
    reviewer_result = await db.execute(select(User).where(User.id == req.reviewed_by_id)) if req.reviewed_by_id else None
    reviewed_by = reviewer_result.scalar_one_or_none() if reviewer_result else None

    return AssetImportRequestRead(
        **_import_request_to_dict(req),
        requested_by_name=f"{requested_by.first_name} {requested_by.last_name}".strip() or requested_by.email if requested_by else None,
        reviewed_by_name=f"{reviewed_by.first_name} {reviewed_by.last_name}".strip() or reviewed_by.email if reviewed_by else None,
    )


@router.patch("/import-requests/{request_id}", response_model=AssetImportRequestRead)
async def review_import_request(
    request_id: int,
    payload: AssetImportRequestReview,
    current_user: CurrentBulkImportDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(AssetImportRequest).where(
            AssetImportRequest.id == request_id,
            AssetImportRequest.organization_id == current_user.organization_id,
        )
    )
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import request not found")

    req.status = payload.status
    req.reviewed_by_id = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.review_notes = payload.review_notes

    # Save the review status first, so it's persisted even if the import fails later
    await db.commit()

    if payload.status == "approved":
        try:
            conn = validate_connection(req.role_arn, None, req.region)
            if not conn["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AWS connection failed: {conn.get('error', 'Unknown error')}",
                )

            result = await import_aws_resources_via_steampipe(
                req.role_arn,
                req.account_name,
                None,
                req.region,
                db,
            )

            svc = IngestionService()
            await svc.ingest_from_result(
                current_user.organization_id,
                result,
                req.region,
                result.get("account_id"),
            )

            # Commit the import data only if everything succeeds
            await db.commit()
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Import failed after review approval: {str(e)}",
            )

    await db.refresh(req)

    user_result = await db.execute(select(User).where(User.id == req.requested_by_id))
    requested_by = user_result.scalar_one_or_none()
    reviewer_result = await db.execute(select(User).where(User.id == req.reviewed_by_id))
    reviewed_by = reviewer_result.scalar_one_or_none()

    return AssetImportRequestRead(
        **_import_request_to_dict(req),
        requested_by_name=f"{requested_by.first_name} {requested_by.last_name}".strip() or requested_by.email if requested_by else None,
        reviewed_by_name=f"{reviewed_by.first_name} {reviewed_by.last_name}".strip() or reviewed_by.email if reviewed_by else None,
    )


@router.post("/suggestions", response_model=AssetSuggestionRead, status_code=status.HTTP_201_CREATED)
async def create_asset_suggestion(payload: AssetSuggestionCreate, current_user: CurrentUserDep, db: DBSessionDep):
    suggestion = AssetSuggestion(
        organization_id=current_user.organization_id,
        suggested_by_id=current_user.id,
        suggested_data=payload.model_dump(),
        status="pending",
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    user_result = await db.execute(select(User).where(User.id == suggestion.suggested_by_id))
    suggested_by = user_result.scalar_one_or_none()
    cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == payload.category_id))
    cat = cat_result.scalar_one_or_none()
    submitter_name = f"{suggested_by.first_name} {suggested_by.last_name}".strip() or suggested_by.email if suggested_by else "A user"

    await notify_admins(
        db,
        current_user.organization_id,
        "New Asset Suggestion",
        f"{submitter_name} suggested adding an asset: {payload.name}",
        notification_type="asset_suggestion",
        reference_type="asset_suggestion",
        reference_id=suggestion.id,
    )
    await db.commit()

    return AssetSuggestionRead(
        **{c.name: getattr(suggestion, c.name) for c in suggestion.__table__.columns},
        suggested_by_name=submitter_name,
        reviewed_by_name=None,
        category_name=cat.name if cat else None,
    )


@router.get("/suggestions", response_model=List[AssetSuggestionRead])
async def list_asset_suggestions(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    is_admin = any(role.name in ("super_admin", "compliance_admin") for role in current_user.roles)

    query = select(AssetSuggestion).where(AssetSuggestion.organization_id == current_user.organization_id)
    if not is_admin:
        query = query.where(AssetSuggestion.suggested_by_id == current_user.id)
    if status_filter:
        query = query.where(AssetSuggestion.status == status_filter)
    query = query.order_by(AssetSuggestion.created_at.desc())

    result = await db.execute(query)
    suggestions = result.scalars().all()

    user_ids = {s.suggested_by_id for s in suggestions} | {s.reviewed_by_id for s in suggestions if s.reviewed_by_id}
    users = {}
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: f"{u.first_name} {u.last_name}".strip() or u.email for u in user_result.scalars().all()}

    category_ids = {s.suggested_data.get("category_id") for s in suggestions if s.suggested_data.get("category_id")}
    categories = {}
    if category_ids:
        cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id.in_(category_ids)))
        categories = {c.id: c.name for c in cat_result.scalars().all()}

    return [
        AssetSuggestionRead(
            **{c.name: getattr(s, c.name) for c in s.__table__.columns},
            suggested_by_name=users.get(s.suggested_by_id),
            reviewed_by_name=users.get(s.reviewed_by_id) if s.reviewed_by_id else None,
            category_name=categories.get(s.suggested_data.get("category_id")),
        )
        for s in suggestions
    ]


@router.get("/suggestions/{suggestion_id}", response_model=AssetSuggestionRead)
async def get_asset_suggestion(suggestion_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(AssetSuggestion).where(
            AssetSuggestion.id == suggestion_id,
            AssetSuggestion.organization_id == current_user.organization_id,
        )
    )
    s = result.scalar_one_or_none()
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    user_result = await db.execute(select(User).where(User.id == s.suggested_by_id))
    suggested_by = user_result.scalar_one_or_none()
    reviewer_result = await db.execute(select(User).where(User.id == s.reviewed_by_id)) if s.reviewed_by_id else None
    reviewed_by = reviewer_result.scalar_one_or_none() if reviewer_result else None
    cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == s.suggested_data.get("category_id")))
    cat = cat_result.scalar_one_or_none()

    return AssetSuggestionRead(
        **{c.name: getattr(s, c.name) for c in s.__table__.columns},
        suggested_by_name=f"{suggested_by.first_name} {suggested_by.last_name}".strip() or suggested_by.email if suggested_by else None,
        reviewed_by_name=f"{reviewed_by.first_name} {reviewed_by.last_name}".strip() or reviewed_by.email if reviewed_by else None,
        category_name=cat.name if cat else None,
    )


@router.patch("/suggestions/{suggestion_id}", response_model=AssetSuggestionRead)
async def review_asset_suggestion(
    suggestion_id: int,
    payload: AssetSuggestionReview,
    current_user: CurrentBulkImportDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(AssetSuggestion).where(
            AssetSuggestion.id == suggestion_id,
            AssetSuggestion.organization_id == current_user.organization_id,
        )
    )
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

    suggestion.status = payload.status
    suggestion.reviewed_by_id = current_user.id
    suggestion.reviewed_at = datetime.now(timezone.utc)
    suggestion.review_notes = payload.review_notes

    if payload.status == "approved":
        data = suggestion.suggested_data
        tags_data = data.pop("tags", None) or []
        owner_id = data.pop("owner_id", None) or suggestion.suggested_by_id
        asset = Asset(organization_id=current_user.organization_id, owner_id=owner_id, **data)
        db.add(asset)
        await db.flush()
        for tag in tags_data:
            db.add(AssetTag(asset_id=asset.id, key=tag.get("key", ""), value=tag.get("value")))

    await db.commit()
    await db.refresh(suggestion)

    user_result = await db.execute(select(User).where(User.id == suggestion.suggested_by_id))
    suggested_by = user_result.scalar_one_or_none()
    reviewer_result = await db.execute(select(User).where(User.id == suggestion.reviewed_by_id))
    reviewed_by = reviewer_result.scalar_one_or_none()
    cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == suggestion.suggested_data.get("category_id")))
    cat = cat_result.scalar_one_or_none()

    return AssetSuggestionRead(
        **{c.name: getattr(suggestion, c.name) for c in suggestion.__table__.columns},
        suggested_by_name=f"{suggested_by.first_name} {suggested_by.last_name}".strip() or suggested_by.email if suggested_by else None,
        reviewed_by_name=f"{reviewed_by.first_name} {reviewed_by.last_name}".strip() or reviewed_by.email if reviewed_by else None,
        category_name=cat.name if cat else None,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: int, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == current_user.organization_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await db.delete(asset)
    await db.commit()
