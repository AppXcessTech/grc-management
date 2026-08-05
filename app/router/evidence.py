from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, CurrentUserDep, DBSessionDep, PermissionRequired
from app.core.tenant import add_org_filter, get_by_id_org_scoped
from app.models.evidence import Evidence
from app.models.user import User
from app.schema.evidence import (
    EvidenceCreate,
    EvidenceRead,
    EvidenceReviewCreate,
    EvidenceReviewRead,
    EvidenceSourceCreate,
    EvidenceSourceRead,
    EvidenceSourceUpdate,
    EvidenceUpdate,
    EvidenceFileRead,
)
from app.services import evidence as service

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


# ---- Sources ----
@router.post("/sources", response_model=EvidenceSourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: EvidenceSourceCreate,
    db: DBSessionDep,
    current_user: CurrentSuperAdminDep,
):
    return await service.create_source(db, payload)


@router.get("/sources", response_model=list[EvidenceSourceRead])
async def list_sources(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    active_only: bool = Query(False),
):
    return await service.list_sources(db, active_only=active_only)


@router.get("/sources/{source_id}", response_model=EvidenceSourceRead)
async def get_source(
    source_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    return await service.get_source(db, source_id)


@router.patch("/sources/{source_id}", response_model=EvidenceSourceRead)
async def update_source(
    source_id: int,
    payload: EvidenceSourceUpdate,
    db: DBSessionDep,
    current_user: CurrentSuperAdminDep,
):
    return await service.update_source(db, source_id, payload)


# ---- Evidence ----
@router.post("/", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    payload: EvidenceCreate,
    db: DBSessionDep,
    current_user: User = Depends(PermissionRequired("evidence", "create")),
):
    return await service.create_evidence(
        db, payload, current_user.organization_id, current_user.id
    )


@router.get("/", response_model=list[EvidenceRead])
async def list_evidence(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    source_id: int | None = None,
    evidence_type: str | None = None,
    control_id: int | None = None,
    requirement_id: int | None = None,
    search: str | None = None,
):
    return await service.list_evidence(
        db,
        organization_id=current_user.organization_id,
        source_id=source_id,
        evidence_type=evidence_type,
        control_id=control_id,
        requirement_id=requirement_id,
        search=search,
    )


@router.get("/{evidence_id}", response_model=EvidenceRead)
async def get_evidence(
    evidence_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return evidence


@router.patch("/{evidence_id}", response_model=EvidenceRead)
async def update_evidence(
    evidence_id: int,
    payload: EvidenceUpdate,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return await service.update_evidence(db, evidence_id, payload)


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await service.delete_evidence(db, evidence_id)
    return None


# ---- Files ----
@router.post("/{evidence_id}/files", response_model=EvidenceFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    evidence_id: int,
    file: UploadFile,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return await service.upload_file(db, evidence_id, file, current_user.id)


@router.get("/{evidence_id}/files", response_model=list[EvidenceFileRead])
async def list_files(
    evidence_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return await service.list_files(db, evidence_id)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    await service.delete_file(db, file_id)
    return None


# ---- Reviews ----
@router.post("/{evidence_id}/reviews", response_model=EvidenceReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    evidence_id: int,
    payload: EvidenceReviewCreate,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return await service.create_review(db, evidence_id, current_user.id, payload)


@router.get("/{evidence_id}/reviews", response_model=list[EvidenceReviewRead])
async def list_reviews(
    evidence_id: int,
    db: DBSessionDep,
    current_user: CurrentUserDep,
):
    evidence = await get_by_id_org_scoped(db, Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return await service.list_reviews(db, evidence_id)
