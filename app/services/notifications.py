from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import InAppNotification
from app.models.user import User
from app.models.role import Role
from app.models.enums import RoleName
from app.models.user_role import UserRole


async def notify_admins(
    db: AsyncSession,
    organization_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    reference_type: str | None = None,
    reference_id: int | None = None,
) -> list[InAppNotification]:
    role_result = await db.execute(
        select(Role.id).where(
            Role.name.in_([RoleName.super_admin, RoleName.compliance_admin]),
            (Role.organization_id == organization_id) | (Role.organization_id.is_(None)),
        )
    )
    role_ids = [r for (r,) in role_result.fetchall()]
    if not role_ids:
        return []

    ur_result = await db.execute(
        select(UserRole.user_id).where(UserRole.role_id.in_(role_ids))
    )
    admin_ids = list({ur for (ur,) in ur_result.fetchall()})

    notifications = []
    for uid in admin_ids:
        n = InAppNotification(
            organization_id=organization_id,
            user_id=uid,
            title=title,
            message=message,
            notification_type=notification_type,
            reference_type=reference_type,
            reference_id=reference_id,
            is_read=False,
        )
        db.add(n)
        notifications.append(n)

    await db.flush()
    return notifications
