from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app import logger
from app.core.config import setup_logger
from app.core.manager import lifespan
from app.core.redis import RedisHelper
from app.core.settings import Settings
from app.core.tenant import current_org_id_var, is_platform_admin_var
from app.router.assets import router as assets_router
from app.router.asset_categories import router as asset_categories_router
from app.router.asset_tags import router as asset_tags_router
from app.router.asset_owners import router as asset_owners_router
from app.router.base import router as base_router
from app.router.vendors import router as vendors_router
from app.router.organizations import router as organizations_router
from app.router.departments import router as departments_router
from app.router.business_units import router as business_units_router
from app.router.users import router as users_router
from app.router.roles import router as roles_router
from app.router.auth import router as auth_router
from app.router.frameworks import router as frameworks_router
from app.router.requirements import router as requirements_router
from app.router.controls import router as controls_router
from app.router.control_mappings import router as control_mappings_router
from app.router.evidence import router as evidence_router
from app.router.policies import router as policies_router
from app.router.overlook.auth import router as overlook_auth_router
from app.router.overlook.organizations import router as overlook_orgs_router

from app.router.subsidiaries import router as subsidiaries_router

from app.router.notifications import router as notifications_router
from app.router.my_departments import router as my_departments_router
from app.router.people_assets import router as people_assets_router
from app.router.endpoint_devices import router as endpoint_devices_router
from app.router.compute_assets import router as compute_assets_router
from app.router.integrations.okta import router as okta_integration_router
from app.router.integrations.manageengine_mdm import router as mdm_integration_router
from app.router.integrations.aws import router as aws_integration_router
from app.router.integrations.azure import router as azure_integration_router
from app.router.integrations.github import router as github_integration_router
from app.router.integrations.generic import router as generic_integration_router
from app.router.integrations.gcp import router as gcp_integration_router
from app.router.integrations.bulk import router as bulk_integration_router
from app.router.integrations.microsoft365 import router as microsoft365_integration_router
from app.router.sso_microsoft import router as sso_microsoft_router
from app.router.canonical_assets import router as canonical_assets_router


_settings = Settings()

app = FastAPI(lifespan=lifespan, debug=_settings.debug, docs_url="/api/docs")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logger(_settings.debug)

uploads_dir = Path("data/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.middleware("http")
async def reset_tenant_context(request, call_next):
    response = await call_next(request)
    current_org_id_var.set(None)
    is_platform_admin_var.set(False)
    return response


app.include_router(base_router)
app.include_router(assets_router)
app.include_router(asset_categories_router)
app.include_router(asset_tags_router)
app.include_router(asset_owners_router)

app.include_router(vendors_router)
app.include_router(organizations_router)
app.include_router(departments_router)
app.include_router(my_departments_router)
app.include_router(business_units_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(auth_router)
app.include_router(frameworks_router)
app.include_router(requirements_router)
app.include_router(controls_router)
app.include_router(control_mappings_router)
app.include_router(evidence_router)
app.include_router(policies_router)

# Overlook Portal Routers
app.include_router(overlook_auth_router, prefix="/api/overlook")
app.include_router(overlook_orgs_router, prefix="/api/overlook")

app.include_router(subsidiaries_router)

app.include_router(notifications_router)
app.include_router(people_assets_router)
app.include_router(endpoint_devices_router)
app.include_router(compute_assets_router)
app.include_router(okta_integration_router)
app.include_router(mdm_integration_router)
app.include_router(sso_microsoft_router)
app.include_router(canonical_assets_router)
app.include_router(aws_integration_router)
app.include_router(azure_integration_router)
app.include_router(bulk_integration_router)
app.include_router(github_integration_router)
app.include_router(generic_integration_router)
app.include_router(gcp_integration_router)
app.include_router(microsoft365_integration_router)

client = TestClient(app)


def add_cache_layer(app: FastAPI) -> None:
    try:
        app.state.cache = RedisHelper()
    except Exception as e:
        logger.error(e)
