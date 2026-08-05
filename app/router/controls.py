from typing import List

from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, DBSessionDep, PermissionRequired
from app.core.tenant import add_org_filter
from app.models.control import Control
from app.models.user import User
from app.models.control_mapping import ControlMapping
from app.models.evidence import Evidence, EvidenceControlLink, EvidenceFile
from app.models.requirement import Requirement
from app.schema.control import Control as ControlSchema, ControlCreate, ControlUpdate, ControlWithEvidenceCount
from app.schema.evidence import EvidenceCreate, EvidenceRead, EvidenceReviewCreate, EvidenceReviewRead, EvidenceFileRead
from app.services.evidence import (
    create_evidence,
    delete_evidence,
    get_evidence,
    upload_file,
    list_files as list_evidence_files,
    create_review,
    list_reviews as list_evidence_reviews,
)

def _numeric_sort_key(c: dict) -> list:
    try:
        parts = c['code'].split('.')
        return [int(x) for x in parts]
    except (ValueError, IndexError):
        return [float('inf'), c['code']]


router = APIRouter(prefix="/api/controls", tags=["controls"])


@router.post("/", response_model=ControlSchema, status_code=status.HTTP_201_CREATED)
async def create_control(current_user: CurrentUserDep, payload: ControlCreate, db: AsyncSession = Depends(get_db)) -> Control:
    if payload.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create control for another organization")

    control = Control(**payload.model_dump())
    db.add(control)
    await db.commit()
    await db.refresh(control)
    return control


@router.get("/", response_model=List[ControlWithEvidenceCount])
async def list_controls(
    current_user: User = Depends(PermissionRequired("control", "view")),
    framework_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    base_filter = []

    if framework_id:
        controls_subq = (
            select(ControlMapping.control_id)
            .join(Requirement, Requirement.id == ControlMapping.requirement_id)
            .where(Requirement.framework_id == framework_id)
            .distinct()
            .subquery()
        )
        base_filter.append(Control.id.in_(select(controls_subq.c.control_id)))

    evidence_count_stmt = (
        select(
            EvidenceControlLink.control_id,
            func.count(EvidenceControlLink.evidence_id).label("cnt")
        )
        .join(Evidence, Evidence.id == EvidenceControlLink.evidence_id)
        .where(Evidence.organization_id == current_user.organization_id)
        .group_by(EvidenceControlLink.control_id)
        .subquery()
    )

    result = await db.execute(
        select(Control, evidence_count_stmt.c.cnt)
        .outerjoin(evidence_count_stmt, Control.id == evidence_count_stmt.c.control_id)
        .where(*base_filter)
    )
    rows = result.all()
    controls = []
    for control, cnt in rows:
        controls.append({
            "id": control.id,
            "organization_id": control.organization_id,
            "code": control.code,
            "name": control.name,
            "description": control.description,
            "status": control.status.value if hasattr(control.status, "value") else control.status,
            "evidence_count": cnt or 0,
        })
    controls.sort(key=_numeric_sort_key)
    return controls


@router.get("/{control_id}", response_model=ControlSchema)
async def get_control(control_id: int, current_user: User = Depends(PermissionRequired("control", "view")), db: AsyncSession = Depends(get_db)) -> Control:
    result = await db.execute(
        select(Control)
        .where(Control.id == control_id)
    )
    control = result.scalar_one_or_none()
    if control is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")
    return control


@router.patch("/{control_id}", response_model=ControlSchema)
async def update_control(current_user: CurrentUserDep, control_id: int, payload: ControlUpdate, db: AsyncSession = Depends(get_db)) -> Control:
    result = await db.execute(
        select(Control)
        .where(Control.id == control_id)
        .where(Control.organization_id == current_user.organization_id)
    )
    control = result.scalar_one_or_none()
    if control is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(control, key, value)

    await db.commit()
    await db.refresh(control)
    return control


@router.delete("/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control(current_user: CurrentUserDep, control_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Control)
        .where(Control.id == control_id)
        .where(Control.organization_id == current_user.organization_id)
    )
    control = result.scalar_one_or_none()
    if control is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")

    await db.delete(control)
    await db.commit()
    return None


# ---- Control Evidence Integration ----

@router.get("/{control_id}/evidence", response_model=List[EvidenceRead])
async def list_control_evidence(
    current_user: CurrentUserDep,
    control_id: int,
    db: AsyncSession = Depends(get_db),
):
    # Verify control belongs to user's org
    await get_control(current_user, control_id, db)

    stmt = (
        select(Evidence)
        .options(
            selectinload(Evidence.files),
            selectinload(Evidence.reviews),
            selectinload(Evidence.controls),
            selectinload(Evidence.requirements),
        )
        .join(EvidenceControlLink, EvidenceControlLink.evidence_id == Evidence.id)
        .where(EvidenceControlLink.control_id == control_id)
        .where(Evidence.organization_id == current_user.organization_id)
        .order_by(Evidence.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{control_id}/evidence", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def create_control_evidence(
    current_user: CurrentUserDep,
    control_id: int,
    payload: EvidenceCreate,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    payload.control_ids = list(set(payload.control_ids + [control_id]))
    return await create_evidence(db, payload, current_user.organization_id, current_user.id)


@router.post("/{control_id}/evidence/upload", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def upload_control_evidence(
    current_user: CurrentUserDep,
    control_id: int,
    name: str = Query(...),
    description: str | None = Query(None),
    file: UploadFile = ...,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)

    # Create evidence with control link
    evidence = Evidence(
        organization_id=current_user.organization_id,
        source_id=1,
        name=name,
        description=description,
        collected_by=current_user.id,
    )
    db.add(evidence)
    await db.flush()

    db.add(EvidenceControlLink(evidence_id=evidence.id, control_id=control_id))

    evidence_file = EvidenceFile(
        evidence_id=evidence.id,
        file_path="",
        file_name=file.filename or "unnamed",
        mime_type=file.content_type,
        uploaded_by=current_user.id,
    )
    db.add(evidence_file)
    await db.flush()

    from app.core.storage import save_upload_file
    file_path = save_upload_file(file, sub_dir="evidence")
    evidence_file.file_path = file_path

    await db.commit()

    result = await db.execute(
        select(Evidence)
        .options(
            selectinload(Evidence.files),
            selectinload(Evidence.reviews),
            selectinload(Evidence.controls),
            selectinload(Evidence.requirements),
        )
        .where(Evidence.id == evidence.id)
    )
    return result.scalar_one()


@router.get("/{control_id}/evidence/{evidence_id}", response_model=EvidenceRead)
async def get_control_evidence(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    return await get_evidence(db, evidence_id)


@router.delete("/{control_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control_evidence(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    await delete_evidence(db, evidence_id)
    return None


# ---- Evidence Files scoped under control ----

@router.post("/{control_id}/evidence/{evidence_id}/files", response_model=EvidenceFileRead, status_code=status.HTTP_201_CREATED)
async def upload_control_evidence_file(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    return await upload_file(db, evidence_id, file, current_user.id)


@router.get("/{control_id}/evidence/{evidence_id}/files", response_model=List[EvidenceFileRead])
async def list_control_evidence_files(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    return await list_evidence_files(db, evidence_id)


@router.get("/{control_id}/evidence/{evidence_id}/files/{file_id}/download")
async def download_control_evidence_file(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)

    stmt = (
        select(EvidenceFile)
        .where(EvidenceFile.id == file_id)
        .where(EvidenceFile.evidence_id == evidence_id)
    )
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()
    if file_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    file_path = file_record.file_path
    if file_path.startswith("s3://"):
        from app.core.storage import get_file_url
        return RedirectResponse(url=get_file_url(file_path))

    local_path = FilePath(file_path)
    if not local_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")

    return FileResponse(
        path=local_path,
        media_type=file_record.mime_type or "application/octet-stream",
        filename=file_record.file_name,
    )


# ---- Evidence Reviews scoped under control ----

@router.post("/{control_id}/evidence/{evidence_id}/reviews", response_model=EvidenceReviewRead, status_code=status.HTTP_201_CREATED)
async def review_control_evidence(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    payload: EvidenceReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    return await create_review(db, evidence_id, current_user.id, payload)


@router.get("/{control_id}/evidence/{evidence_id}/reviews", response_model=List[EvidenceReviewRead])
async def list_control_evidence_reviews(
    current_user: CurrentUserDep,
    control_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
):
    await get_control(current_user, control_id, db)
    return await list_evidence_reviews(db, evidence_id)
