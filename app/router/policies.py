from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, PermissionRequired
from app.core.storage import save_upload_file, delete_file
from app.models.policy import Policy
from app.models.user import User
from app.models.policy_version import PolicyVersion
from app.models.policy_review import PolicyReview
from app.models.policy_acknowledgement import PolicyAcknowledgement
from app.models.enums import PolicyStatus, ReviewStatus, PolicyCategory
from app.schema.policy import Policy as PolicySchema, PolicyCreate, PolicyUpdate
from app.schema.policy_version import PolicyVersion as PolicyVersionSchema
from app.schema.policy_acknowledgement import PolicyAcknowledgement as AcknowledgementSchema

router = APIRouter(prefix="/api/policies", tags=["policies"])


from sqlalchemy.orm import selectinload


@router.post("/", response_model=PolicySchema, status_code=status.HTTP_201_CREATED)
async def create_policy(
    current_user: User = Depends(PermissionRequired("policy", "edit")),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    category: PolicyCategory = Form(PolicyCategory.other),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
) -> Policy:
    policy = Policy(
        name=name,
        description=description,
        category=category,
        organization_id=current_user.organization_id,
        status=PolicyStatus.draft
    )
    db.add(policy)
    await db.flush()
    
    if file:
        file_path = save_upload_file(file, sub_dir=f"policies/{policy.id}")
        version = PolicyVersion(
            policy_id=policy.id,
            version_number=1,
            file_path=file_path,
            notes="Initial version",
            created_by_id=current_user.id
        )
        db.add(version)
    
    policy_id = policy.id
    await db.commit()
    
    # Fetch with versions
    result = await db.execute(
        select(Policy)
        .where(Policy.id == policy_id)
        .options(selectinload(Policy.versions))
    )
    return result.scalar_one()


@router.get("/", response_model=List[PolicySchema])
async def list_policies(
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db)
) -> List[Policy]:
    result = await db.execute(
        select(Policy)
        .where(Policy.organization_id == current_user.organization_id)
        .options(selectinload(Policy.versions))
    )
    return result.scalars().all()


@router.get("/{policy_id}", response_model=PolicySchema)
async def get_policy(
    policy_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db)
) -> Policy:
    result = await db.execute(
        select(Policy).where(
            and_(
                Policy.id == policy_id,
                Policy.organization_id == current_user.organization_id
            )
        ).options(selectinload(Policy.versions))
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicySchema)
async def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    current_user: User = Depends(PermissionRequired("policy", "edit")),
    db: AsyncSession = Depends(get_db)
) -> Policy:
    result = await db.execute(
        select(Policy).where(
            and_(
                Policy.id == policy_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)
    
    await db.commit()
    
    # Re-fetch with versions to avoid refresh error and provide complete data
    result = await db.execute(
        select(Policy)
        .where(Policy.id == policy_id)
        .options(selectinload(Policy.versions))
    )
    return result.scalar_one()


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionRequired("policy", "edit")),
):
    result = await db.execute(
        select(Policy).where(
            and_(
                Policy.id == policy_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    await db.delete(policy)
    await db.commit()
    return None


@router.post("/{policy_id}/versions", response_model=PolicyVersionSchema, status_code=status.HTTP_201_CREATED)
async def create_policy_version(
    policy_id: int,
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionRequired("policy", "edit")),
) -> PolicyVersion:
    result = await db.execute(
        select(Policy).where(
            and_(
                Policy.id == policy_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    # Get latest version number
    result = await db.execute(
        select(PolicyVersion)
        .where(PolicyVersion.policy_id == policy_id)
        .order_by(PolicyVersion.version_number.desc())
        .limit(1)
    )
    latest_version = result.scalar_one_or_none()
    new_version_number = (latest_version.version_number + 1) if latest_version else 1
    
    file_path = save_upload_file(file, sub_dir=f"policies/{policy_id}")
    
    version = PolicyVersion(
        policy_id=policy_id,
        version_number=new_version_number,
        file_path=file_path,
        notes=notes,
        created_by_id=current_user.id
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


@router.get("/{policy_id}/versions", response_model=List[PolicyVersionSchema])
async def list_policy_versions(
    policy_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db)
) -> List[PolicyVersion]:
    result = await db.execute(
        select(Policy).where(
            and_(
                Policy.id == policy_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    result = await db.execute(
        select(PolicyVersion).where(PolicyVersion.policy_id == policy_id)
    )
    return result.scalars().all()


@router.post("/versions/{version_id}/publish", response_model=PolicyVersionSchema)
async def publish_policy_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionRequired("policy", "edit")),
) -> PolicyVersion:
    # Joining with Policy to check organization
    result = await db.execute(
        select(PolicyVersion)
        .join(Policy)
        .where(
            and_(
                PolicyVersion.id == version_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy version not found")
    
    version.published_at = datetime.now()
    
    # Update policy status to published
    policy_result = await db.execute(select(Policy).where(Policy.id == version.policy_id))
    policy = policy_result.scalar_one()
    policy.status = PolicyStatus.published
    
    await db.commit()
    await db.refresh(version)
    return version


@router.post("/versions/{version_id}/acknowledge", response_model=AcknowledgementSchema, status_code=status.HTTP_201_CREATED)
async def acknowledge_policy_version(
    version_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db)
) -> PolicyAcknowledgement:
    # Join with Policy to check organization
    result = await db.execute(
        select(PolicyVersion)
        .join(Policy)
        .where(
            and_(
                PolicyVersion.id == version_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy version not found")
    
    if not version.published_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot acknowledge an unpublished policy version")

    # Check if already acknowledged
    ack_result = await db.execute(
        select(PolicyAcknowledgement).where(
            and_(
                PolicyAcknowledgement.policy_version_id == version_id,
                PolicyAcknowledgement.user_id == current_user.id
            )
        )
    )
    existing_ack = ack_result.scalar_one_or_none()
    if existing_ack:
        return existing_ack

    acknowledgement = PolicyAcknowledgement(
        policy_version_id=version_id,
        user_id=current_user.id
    )
    db.add(acknowledgement)
    await db.commit()
    await db.refresh(acknowledgement)
    return acknowledgement


@router.get("/{policy_id}/acknowledgements", response_model=List[AcknowledgementSchema])
async def list_policy_acknowledgements(
    policy_id: int,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db)
) -> List[PolicyAcknowledgement]:
    result = await db.execute(
        select(Policy).where(
            and_(
                Policy.id == policy_id,
                Policy.organization_id == current_user.organization_id
            )
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    
    result = await db.execute(
        select(PolicyAcknowledgement)
        .join(PolicyVersion)
        .where(PolicyVersion.policy_id == policy_id)
    )
    return result.scalars().all()
