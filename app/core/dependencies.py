from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db, get_db_connect
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.tenant import tenant_context
from app.models.enums import RoleName, UserStatus
from app.models.user import User
from app.models.platform_user import PlatformUser
from app.models.permission import Permission
from app.models.role_permission import RolePermission

# For ORM queries
DBSessionDep = Annotated[AsyncSession, Depends(get_db)]

# For Raw SQL queries
DBConnectionDep = Annotated[AsyncConnection, Depends(get_db_connect)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}",
        )

    await tenant_context(org_id=user.organization_id).__aenter__()
    return user

CurrentUserDep = Annotated[User, Depends(get_current_user)]

async def get_current_platform_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
) -> PlatformUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate platform credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        scope: str = payload.get("scope")
        if email is None or scope != "platform":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(select(PlatformUser).where(PlatformUser.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    await tenant_context(org_id=None, platform=True).__aenter__()
    return user

CurrentPlatformUserDep = Annotated[PlatformUser, Depends(get_current_platform_user)]


async def require_super_admin(
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> User:
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user or not any(role.name == RoleName.super_admin for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return user


CurrentSuperAdminDep = Annotated[User, Depends(require_super_admin)]


async def require_bulk_import_access(
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> User:
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user or not any(role.name in (RoleName.super_admin, RoleName.compliance_admin) for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return user


CurrentBulkImportDep = Annotated[User, Depends(require_bulk_import_access)]


class PermissionRequired:
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    async def __call__(
        self,
        current_user: CurrentUserDep,
        db: DBSessionDep,
    ) -> User:
        result = await db.execute(
            select(User).where(User.id == current_user.id).options(selectinload(User.roles))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        role_ids = [r.id for r in user.roles]
        if not role_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

        perm_check = await db.execute(
            select(RolePermission)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                RolePermission.role_id.in_(role_ids),
                Permission.resource == self.resource,
                Permission.action == self.action,
            )
            .limit(1)
        )
        if not perm_check.first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

        return user
