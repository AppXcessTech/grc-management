import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

from datetime import datetime, timezone

# Mock database session
class MockDB:
    def add(self, item):
        pass
    async def commit(self):
        pass
    async def flush(self):
        pass
    async def refresh(self, item):
        item.id = 1
        if hasattr(item, "created_at"):
            item.created_at = datetime.now(timezone.utc)
        if hasattr(item, "updated_at"):
            item.updated_at = datetime.now(timezone.utc)
        if hasattr(item, "external_id") and getattr(item, "external_id") is None:
            import uuid
            item.external_id = str(uuid.uuid4())
    async def execute(self, query):
        class Result:
            def scalar_one_or_none(self):
                return None
            def scalars(self):
                class Scalars:
                    def all(self):
                        return []
                return Scalars()
        return Result()

async def override_get_db():
    yield MockDB()

async def override_get_current_user():
    from app.models.user import User
    from app.models.enums import UserStatus, RoleName
    from app.models.role import Role
    user = User(
        id=1,
        email="test@test.com",
        first_name="Test",
        last_name="User",
        organization_id=1,
        status=UserStatus.active
    )
    role = Role(id=1, name=RoleName.super_admin, organization_id=1)
    user.roles = [role]
    return user

async def override_require_super_admin():
    from app.models.user import User
    from app.models.enums import UserStatus, RoleName
    from app.models.role import Role
    user = User(
        id=1,
        email="test@test.com",
        first_name="Test",
        last_name="User",
        organization_id=1,
        status=UserStatus.active
    )
    role = Role(id=1, name=RoleName.super_admin, organization_id=1)
    user.roles = [role]
    return user

from app.core.dependencies import get_current_user, require_super_admin

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[require_super_admin] = override_require_super_admin

client = TestClient(app)

def test_create_organization():
    response = client.post(
        "/api/organizations/",
        json={"name": "Test Org", "slug": "test-org", "domain": "test.com"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Org"
    assert response.json()["slug"] == "test-org"

def test_invite_user():
    response = client.post(
        "/api/users/invite",
        json={
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "User",
            "organization_id": 1
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@test.com"
    assert response.json()["status"] == "active"
