from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update

from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.notification import InAppNotification
from app.schema.notification import NotificationRead

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationRead])
async def list_notifications(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    unread_only: bool = False,
):
    query = select(InAppNotification).where(
        InAppNotification.user_id == current_user.id,
        InAppNotification.organization_id == current_user.organization_id,
    )
    if unread_only:
        query = query.where(InAppNotification.is_read == False)
    query = query.order_by(InAppNotification.created_at.desc()).limit(50)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/unread-count")
async def unread_count(
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(InAppNotification).where(
            InAppNotification.user_id == current_user.id,
            InAppNotification.organization_id == current_user.organization_id,
            InAppNotification.is_read == False,
        )
    )
    count = len(result.scalars().all())
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    result = await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == current_user.id,
        )
    )
    n = result.scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    n.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    await db.execute(
        update(InAppNotification)
        .where(
            InAppNotification.user_id == current_user.id,
            InAppNotification.organization_id == current_user.organization_id,
            InAppNotification.is_read == False,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}
