import contextvars
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import Select

current_org_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "current_org_id", default=None
)
is_platform_admin_var: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "is_platform_admin", default=False
)


def get_current_org_id() -> int | None:
    return current_org_id_var.get()


def is_platform() -> bool:
    return is_platform_admin_var.get()


@asynccontextmanager
async def tenant_context(org_id: int | None, platform: bool = False) -> AsyncIterator[None]:
    token_org = current_org_id_var.set(org_id)
    token_plat = is_platform_admin_var.set(platform)
    try:
        yield
    finally:
        try:
            current_org_id_var.reset(token_org)
        except ValueError:
            pass
        try:
            is_platform_admin_var.reset(token_plat)
        except ValueError:
            pass


def add_org_filter(query: Select, model: Any, org_id: int | None = None) -> Select:
    """Add an organization_id WHERE clause if the model has the column.

    If org_id is None and a tenant context is active, uses that.
    If is_platform_admin is True, skips filtering (platform admin sees all).
    """
    if is_platform():
        return query
    if not hasattr(model, "organization_id"):
        return query
    if org_id is None:
        org_id = get_current_org_id()
    if org_id is not None:
        query = query.where(model.organization_id == org_id)
    return query


async def get_by_id_org_scoped(db: Any, model: Any, record_id: int, org_id: int | None = None) -> Any | None:
    """Fetch a record by ID, scoped to the current organization."""
    from sqlalchemy import select
    query = select(model).where(model.id == record_id)
    query = add_org_filter(query, model, org_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def assert_org_access(db: Any, model: Any, record_id: int, org_id: int | None = None) -> Any:
    """Fetch a record and raise 404 if not found or not in org scope."""
    from fastapi import HTTPException, status
    record = await get_by_id_org_scoped(db, model, record_id, org_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return record
