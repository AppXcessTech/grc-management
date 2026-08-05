from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status, UploadFile, File
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, CurrentUserDep, DBSessionDep
from app.core.storage import save_upload_file
from app.models.audit_log import AuditLog
from app.models.people_asset import PeopleAsset
from app.models.people_asset_review import PeopleAssetReview
from app.models.user import User
from app.schema.people_asset import PeopleAssetCreate, PeopleAssetRead, PeopleAssetReviewRead, PeopleAssetUpdate

router = APIRouter(prefix="/api/people-assets", tags=["people-assets"])


@router.get("/", response_model=List[PeopleAssetRead])
async def list_people_assets(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    search: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_dir: str = Query("asc"),
):
    query = select(PeopleAsset).where(PeopleAsset.organization_id == current_user.organization_id)

    if not include_archived:
        query = query.where(PeopleAsset.archived_at.is_(None))

    if search:
        like = f"%{search}%"
        query = query.where(
            or_(
                PeopleAsset.name.ilike(like),
                PeopleAsset.email.ilike(like),
                PeopleAsset.job_title.ilike(like),
                PeopleAsset.department.ilike(like),
            )
        )
    if asset_type:
        query = query.where(PeopleAsset.asset_type == asset_type)
    if department:
        query = query.where(PeopleAsset.department == department)
    if status:
        query = query.where(PeopleAsset.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    sort_col = getattr(PeopleAsset, sort_by, PeopleAsset.name)
    if sort_dir == "desc":
        sort_col = sort_col.desc()
    query = query.order_by(sort_col)

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        PeopleAssetRead.model_validate(p) for p in items
    ]


@router.get("/types")
async def list_asset_types():
    return [
        "Employee", "Contractor", "Consultant", "Intern",
        "Temporary Staff", "Third-Party User", "Vendor User",
        "Service Account", "Shared Account", "Privileged Account",
        "Administrator", "Developer", "Security Personnel",
    ]


@router.get("/departments")
async def list_departments(current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(PeopleAsset.department)
        .where(
            PeopleAsset.organization_id == current_user.organization_id,
            PeopleAsset.department.is_not(None),
            PeopleAsset.archived_at.is_(None),
        )
        .distinct()
        .order_by(PeopleAsset.department)
    )
    return [row[0] for row in result.all()]


@router.get("/counts")
async def people_asset_counts(current_user: CurrentUserDep, db: DBSessionDep):
    base = select(PeopleAsset).where(PeopleAsset.organization_id == current_user.organization_id)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0

    active_q = base.where(PeopleAsset.status == "Active", PeopleAsset.archived_at.is_(None))
    active = (await db.execute(select(func.count()).select_from(active_q.subquery()))).scalar() or 0

    inactive_q = base.where(PeopleAsset.status == "Inactive", PeopleAsset.archived_at.is_(None))
    inactive = (await db.execute(select(func.count()).select_from(inactive_q.subquery()))).scalar() or 0

    archived_q = base.where(PeopleAsset.archived_at.is_not(None))
    archived = (await db.execute(select(func.count()).select_from(archived_q.subquery()))).scalar() or 0

    type_q = (
        select(PeopleAsset.asset_type, func.count().label("count"))
        .where(PeopleAsset.organization_id == current_user.organization_id, PeopleAsset.archived_at.is_(None))
        .group_by(PeopleAsset.asset_type)
        .order_by(func.count().desc())
    )
    type_rows = (await db.execute(type_q)).all()
    by_type = {r.asset_type: r.count for r in type_rows}

    return {"total": total, "active": active, "inactive": inactive, "archived": archived, "by_type": by_type}


@router.post("/upload")
async def upload_people_file(file: UploadFile = File(...)):
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    MAX_SIZE = 10 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")
    await file.seek(0)
    file_path = save_upload_file(file, sub_dir="people")
    return {"url": file_path}


@router.get("/{people_asset_id}", response_model=PeopleAssetRead)
async def get_people_asset(people_asset_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.id == people_asset_id,
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="People asset not found")
    return PeopleAssetRead.model_validate(item)


@router.post("/", response_model=PeopleAssetRead, status_code=status.HTTP_201_CREATED)
async def create_people_asset(
    payload: PeopleAssetCreate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    asset = PeopleAsset(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(asset)
    await db.flush()

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="created",
        resource_type="people_asset",
        resource_id=str(asset.id),
        new_values=payload.model_dump(mode="json"),
    ))
    await db.commit()
    await db.refresh(asset)
    return PeopleAssetRead.model_validate(asset)


@router.patch("/{people_asset_id}", response_model=PeopleAssetRead)
async def update_people_asset(
    people_asset_id: int,
    payload: PeopleAssetUpdate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.id == people_asset_id,
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="People asset not found")

    old_values = {
        c.name: getattr(asset, c.name).isoformat() if isinstance(getattr(asset, c.name), datetime) else getattr(asset, c.name)
        for c in asset.__table__.columns
    }
    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(asset, key, val)
    asset.updated_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="updated",
        resource_type="people_asset",
        resource_id=str(asset.id),
        old_values=old_values,
        new_values=payload.model_dump(exclude_unset=True, mode="json"),
    ))
    await db.commit()
    await db.refresh(asset)
    return PeopleAssetRead.model_validate(asset)


@router.post("/{people_asset_id}/archive", response_model=PeopleAssetRead)
async def archive_people_asset(people_asset_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.id == people_asset_id,
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="People asset not found")

    asset.archived_at = datetime.now(timezone.utc)
    asset.status = "Inactive"

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="archived",
        resource_type="people_asset",
        resource_id=str(asset.id),
    ))
    await db.commit()
    await db.refresh(asset)
    return PeopleAssetRead.model_validate(asset)


@router.post("/{people_asset_id}/restore", response_model=PeopleAssetRead)
async def restore_people_asset(people_asset_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.id == people_asset_id,
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="People asset not found")

    asset.archived_at = None
    asset.status = "Active"

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="restored",
        resource_type="people_asset",
        resource_id=str(asset.id),
    ))
    await db.commit()
    await db.refresh(asset)
    return PeopleAssetRead.model_validate(asset)


@router.post("/{people_asset_id}/review", response_model=PeopleAssetReviewRead)
async def review_people_asset(
    people_asset_id: int,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.id == people_asset_id,
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="People asset not found")

    now = datetime.now(timezone.utc)
    asset.last_access_review = now
    asset.last_reviewed_by = current_user.id

    review = PeopleAssetReview(
        people_asset_id=asset.id,
        reviewed_by=current_user.id,
        reviewed_at=now,
    )
    db.add(review)

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="access_reviewed",
        resource_type="people_asset",
        resource_id=str(asset.id),
        new_values={"last_access_review": now.isoformat()},
    ))
    await db.commit()
    await db.refresh(review)
    return PeopleAssetReviewRead.model_validate(review)


@router.get("/{people_asset_id}/reviews", response_model=List[PeopleAssetReviewRead])
async def list_people_asset_reviews(
    people_asset_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(PeopleAssetReview)
        .where(PeopleAssetReview.people_asset_id == people_asset_id)
        .order_by(PeopleAssetReview.reviewed_at.desc())
    )
    reviews = result.scalars().all()
    return [PeopleAssetReviewRead.model_validate(r) for r in reviews]


@router.delete("/{people_asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_people_asset(people_asset_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    user_result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = user_result.scalar_one_or_none()
    is_admin = any(role.name in ("super_admin", "compliance_admin") for role in user.roles) if user else False
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete people assets")

    result = await db.execute(
        select(PeopleAsset).where(
            PeopleAsset.id == people_asset_id,
            PeopleAsset.organization_id == current_user.organization_id,
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="People asset not found")

    db.add(AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="deleted",
        resource_type="people_asset",
        resource_id=str(asset.id),
        old_values={"name": asset.name, "email": asset.email, "asset_type": asset.asset_type},
    ))
    await db.delete(asset)
    await db.commit()
