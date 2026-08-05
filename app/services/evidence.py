from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.storage import save_upload_file
from app.models.evidence import (
    Evidence,
    EvidenceControlLink,
    EvidenceFile,
    EvidenceRequirementLink,
    EvidenceReview,
    EvidenceSource,
)
from app.schema.evidence import EvidenceCreate, EvidenceUpdate


# ---- Sources ----
async def create_source(db: AsyncSession, payload) -> EvidenceSource:
    source = EvidenceSource(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def list_sources(db: AsyncSession, active_only: bool = False) -> list[EvidenceSource]:
    stmt = select(EvidenceSource).order_by(EvidenceSource.name)
    if active_only:
        stmt = stmt.where(EvidenceSource.is_active.is_(True))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_source(db: AsyncSession, source_id: int) -> EvidenceSource:
    result = await db.execute(select(EvidenceSource).where(EvidenceSource.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence source not found")
    return source


async def update_source(db: AsyncSession, source_id: int, payload) -> EvidenceSource:
    source = await get_source(db, source_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    await db.commit()
    await db.refresh(source)
    return source


# ---- Evidence ----
async def create_evidence(
    db: AsyncSession, payload: EvidenceCreate, organization_id: int, user_id: int
) -> Evidence:
    evidence = Evidence(
        organization_id=organization_id,
        source_id=payload.source_id,
        name=payload.name,
        description=payload.description,
        evidence_type=payload.evidence_type,
        collected_by=user_id,
    )
    db.add(evidence)
    await db.flush()

    for cid in payload.control_ids:
        db.add(EvidenceControlLink(evidence_id=evidence.id, control_id=cid))
    for rid in payload.requirement_ids:
        db.add(EvidenceRequirementLink(evidence_id=evidence.id, requirement_id=rid))

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


async def get_evidence(db: AsyncSession, evidence_id: int) -> Evidence:
    stmt = (
        select(Evidence)
        .options(
            selectinload(Evidence.files),
            selectinload(Evidence.reviews),
            selectinload(Evidence.controls),
            selectinload(Evidence.requirements),
        )
        .where(Evidence.id == evidence_id)
    )
    result = await db.execute(stmt)
    evidence = result.scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


async def list_evidence(
    db: AsyncSession,
    organization_id: int | None = None,
    source_id: int | None = None,
    evidence_type: str | None = None,
    control_id: int | None = None,
    requirement_id: int | None = None,
    search: str | None = None,
) -> list[Evidence]:
    stmt = (
        select(Evidence)
        .options(
            selectinload(Evidence.files),
            selectinload(Evidence.reviews),
            selectinload(Evidence.controls),
            selectinload(Evidence.requirements),
        )
        .order_by(Evidence.created_at.desc())
    )
    if organization_id:
        stmt = stmt.where(Evidence.organization_id == organization_id)
    if source_id:
        stmt = stmt.where(Evidence.source_id == source_id)
    if evidence_type:
        stmt = stmt.where(Evidence.evidence_type == evidence_type)
    if control_id:
        stmt = stmt.join(EvidenceControlLink).where(EvidenceControlLink.control_id == control_id)
    if requirement_id:
        stmt = stmt.join(EvidenceRequirementLink).where(EvidenceRequirementLink.requirement_id == requirement_id)
    if search:
        stmt = stmt.where(
            Evidence.name.ilike(f"%{search}%") | Evidence.description.ilike(f"%{search}%")
        )
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_evidence(db: AsyncSession, evidence_id: int, payload: EvidenceUpdate) -> Evidence:
    evidence = await get_evidence(db, evidence_id)
    update_data = payload.model_dump(exclude_unset=True)

    control_ids = update_data.pop("control_ids", None)
    requirement_ids = update_data.pop("requirement_ids", None)

    for key, value in update_data.items():
        setattr(evidence, key, value)

    if control_ids is not None:
        await db.execute(
            delete(EvidenceControlLink).where(EvidenceControlLink.evidence_id == evidence_id)
        )
        for cid in control_ids:
            db.add(EvidenceControlLink(evidence_id=evidence.id, control_id=cid))

    if requirement_ids is not None:
        await db.execute(
            delete(EvidenceRequirementLink).where(EvidenceRequirementLink.evidence_id == evidence_id)
        )
        for rid in requirement_ids:
            db.add(EvidenceRequirementLink(evidence_id=evidence.id, requirement_id=rid))

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


async def delete_evidence(db: AsyncSession, evidence_id: int) -> None:
    evidence = await get_evidence(db, evidence_id)
    await db.delete(evidence)
    await db.commit()


# ---- Evidence Files ----
async def upload_file(
    db: AsyncSession, evidence_id: int, file: UploadFile, user_id: int
) -> EvidenceFile:
    evidence = await get_evidence(db, evidence_id)
    file_path = save_upload_file(file, sub_dir="evidence")
    evidence_file = EvidenceFile(
        evidence_id=evidence.id,
        file_path=file_path,
        file_name=file.filename or "unnamed",
        file_size=None,
        mime_type=file.content_type,
        uploaded_by=user_id,
    )
    db.add(evidence_file)
    await db.commit()
    await db.refresh(evidence_file)
    return evidence_file


async def list_files(db: AsyncSession, evidence_id: int) -> list[EvidenceFile]:
    result = await db.execute(
        select(EvidenceFile).where(EvidenceFile.evidence_id == evidence_id).order_by(EvidenceFile.created_at.desc())
    )
    return result.scalars().all()


async def delete_file(db: AsyncSession, file_id: int) -> None:
    result = await db.execute(select(EvidenceFile).where(EvidenceFile.id == file_id))
    evidence_file = result.scalar_one_or_none()
    if evidence_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    from app.core.storage import delete_file as delete_storage_file
    delete_storage_file(evidence_file.file_path)
    await db.delete(evidence_file)
    await db.commit()


# ---- Evidence Reviews ----
async def create_review(
    db: AsyncSession, evidence_id: int, reviewer_id: int, payload
) -> EvidenceReview:
    evidence = await get_evidence(db, evidence_id)
    review = EvidenceReview(
        evidence_id=evidence.id,
        reviewer_id=reviewer_id,
        status=payload.status,
        comment=payload.comment,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def list_reviews(db: AsyncSession, evidence_id: int) -> list[EvidenceReview]:
    result = await db.execute(
        select(EvidenceReview)
        .where(EvidenceReview.evidence_id == evidence_id)
        .order_by(EvidenceReview.created_at.desc())
    )
    return result.scalars().all()
