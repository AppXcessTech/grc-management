"""Generic integration config router for services that don't have custom sync logic yet.

Stores and retrieves provider-specific connection config as JSON.
Providers like AWS, Azure, Okta, ManageEngine have their own dedicated routers.

For providers with a dedicated router (e.g. Okta), the generic endpoints act as a
bridge — they store config in both the generic location AND the dedicated config
directory so that both the config form and the actual sync engine can find it.

Secret fields (type: 'password') are NEVER returned in plaintext from GET /config.
Instead, they are masked with the SENTINEL placeholder "••••••••".
On POST /setup, if a field value equals the sentinel or is empty, the existing
stored value is preserved — matching the GitHub Actions write-once pattern.
"""
import json
import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.dependencies import CurrentUserDep
from app.router.integrations.base import load_config, save_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations/generic", tags=["integrations"])

# Sentinel value indicating a secret exists but should not be displayed
SECRET_SENTINEL = "••••••••"

# ---------------------------------------------------------------------------
# Dedicated config directories for providers that have real import/sync logic
# ---------------------------------------------------------------------------
DEDICATED_CONFIG_DIRS: dict[str, Path] = {
    "okta": Path("data/okta_config"),
    "github": Path("data/github_config"),
    "gitlab": Path("data/gitlab_config"),
    "microsoft365": Path("data/microsoft365_config"),
    "bitbucket": Path("data/bitbucket_config"),
    "slack": Path("data/slack_config"),
    # Frontend sends "teams" as the provider slug for Microsoft Teams
    "teams": Path("data/microsoft365_config"),
}

# ---------------------------------------------------------------------------
# Providers that support real connection validation (API call)
# ---------------------------------------------------------------------------
TESTABLE_PROVIDERS = {"okta", "github", "gitlab", "microsoft365", "teams", "bitbucket", "slack"}


class GenericSetupRequest(BaseModel):
    config: dict[str, Any]


class GenericConfigResponse(BaseModel):
    config: dict[str, Any]
    configured: bool


class TestResult(BaseModel):
    success: bool
    message: str = ""


def _mask_secret_fields(cfg: dict, secret_fields: list[str]) -> dict:
    """Replace secret field values with the sentinel placeholder.

    If the field exists and has a non-empty value, replace it with SECRET_SENTINEL.
    This prevents real secret values from being returned to the frontend.
    """
    masked = dict(cfg)
    for field in secret_fields:
        if field in masked and masked[field]:
            masked[field] = SECRET_SENTINEL
    return masked


def _merge_secret_fields(
    incoming: dict,
    existing: dict,
    secret_fields: list[str],
) -> dict:
    """Merge incoming config with existing secrets.

    If an incoming secret field value is the sentinel or empty, use the existing
    stored value instead. This allows the frontend to send empty/placeholder
    values for secrets that should be preserved.
    """
    merged = dict(incoming)
    for field in secret_fields:
        val = merged.get(field, "")
        if not val or val == SECRET_SENTINEL:
            if field in existing and existing[field]:
                merged[field] = existing[field]
            else:
                merged.pop(field, None)
    return merged


def _sync_to_dedicated_config(provider: str, org_id: int, cfg: dict) -> None:
    """For known providers, mirror the saved config to their dedicated config dir.

    This ensures that the actual import/sync engine (which reads from the
    dedicated directory) can find the credentials the user set up via the
    generic integration form.
    """
    dedicated_dir = DEDICATED_CONFIG_DIRS.get(provider)
    if dedicated_dir is None:
        return  # no dedicated directory for this provider

    dedicated_dir.mkdir(parents=True, exist_ok=True)
    path = dedicated_dir / f"org_{org_id}.json"

    # For Okta, remap the generic field names to the dedicated router's names
    if provider == "okta":
        dedicated_cfg = {
            "okta_domain": cfg.get("okta_domain", "").strip(),
            "okta_token": cfg.get("okta_token", "").strip(),
        }
    elif provider == "github":
        # The generic form uses field name "token", so we check both names
        github_token = cfg.get("github_token", "") or cfg.get("token", "")
        classic_token = cfg.get("classic_token", "") or cfg.get("classic_token", "")
        dedicated_cfg = {
            "github_token": github_token.strip(),
            "classic_token": classic_token.strip(),
            "account_name": cfg.get("account_name", "").strip(),
        }
    elif provider == "gitlab":
        # The generic form uses fields "baseurl" + "token"; accept legacy names too
        dedicated_cfg = {
            "baseurl": (
                cfg.get("baseurl", "")
                or cfg.get("base_url", "")
                or cfg.get("gitlab_url", "")
            ).strip(),
            "token": (cfg.get("token", "") or cfg.get("gitlab_token", "")).strip(),
        }
    elif provider == "microsoft365" or provider == "teams":
        dedicated_cfg = {
            "tenant_id": cfg.get("tenant_id", "").strip(),
            "client_id": cfg.get("client_id", "").strip(),
            "client_secret": cfg.get("client_secret", "").strip(),
        }
    elif provider == "bitbucket":
        # The generic form uses fields "base_url" + "username" + "password".
        # Bitbucket authenticates with the Atlassian account email plus an API
        # token (app passwords were removed on July 28, 2026).
        dedicated_cfg = {
            "base_url": (cfg.get("base_url", "") or "https://api.bitbucket.org/2.0").strip(),
            "username": cfg.get("username", "").strip(),
            "password": cfg.get("password", "").strip(),
            "workspace_slug": (cfg.get("workspace_slug") or "").strip(),
        }
    elif provider == "slack":
        # The generic form uses fields "profile" (workspace name/domain) + "token".
        dedicated_cfg = {
            "profile": cfg.get("profile", "").strip(),
            "token": (cfg.get("token", "") or cfg.get("slack_token", "")).strip(),
        }
    else:
        dedicated_cfg = dict(cfg)

    path.write_text(json.dumps(dedicated_cfg, indent=2))
    logger.info(
        "Synced %s config to dedicated directory for org %s",
        provider, org_id,
    )


async def _test_okta_connection(cfg: dict) -> TestResult:
    """Actually validate Okta credentials by calling the /api/v1/users endpoint."""
    okta_domain = cfg.get("okta_domain", "").strip()
    okta_token = cfg.get("okta_token", "").strip()

    if not okta_domain or not okta_token:
        return TestResult(
            success=False,
            message="Okta domain and API token are required.",
        )

    # Normalise domain
    okta_domain = (
        okta_domain.removeprefix("https://")
        .removeprefix("http://")
        .split("/")[0]
    )

    url = f"https://{okta_domain}/api/v1/users?limit=1"
    headers = {
        "Authorization": f"SSWS {okta_token}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 200:
            return TestResult(
                success=True,
                message=f"Okta connection successful! Domain: {okta_domain}. "
                        f"API token is valid.",
            )
        elif resp.status_code == 401:
            return TestResult(
                success=False,
                message="Okta authentication failed (401). "
                        "Check that your API token is valid and has not expired.",
            )
        elif resp.status_code == 403:
            return TestResult(
                success=False,
                message="Okta access denied (403). "
                        "Your API token may lack the required permissions.",
            )
        else:
            return TestResult(
                success=False,
                message=f"Okta API returned HTTP {resp.status_code}: "
                        f"{resp.text[:200]}",
            )
    except httpx.ConnectError:
        return TestResult(
            success=False,
            message=f"Could not connect to {okta_domain}. "
                    "Check that the Okta domain is correct.",
        )
    except httpx.TimeoutException:
        return TestResult(
            success=False,
            message=f"Connection to {okta_domain} timed out. "
                    "Check network connectivity and firewall rules.",
        )
    except Exception as e:
        logger.exception("Okta connection test failed unexpectedly")
        return TestResult(
            success=False,
            message=f"Connection test failed: {str(e)[:200]}",
        )


async def _test_github_connection(cfg: dict) -> TestResult:
    """Validate GitHub credentials via Steampipe."""
    # Generic form sends field as "token", dedicated router sends as "github_token"
    github_token = (cfg.get("github_token", "") or cfg.get("token", "")).strip()

    if not github_token:
        return TestResult(
            success=False,
            message="GitHub personal access token is required.",
        )

    try:
        from app.services.steampipe_github import validate_github_connection
        result = validate_github_connection(github_token)
        if result.get("success"):
            return TestResult(
                success=True,
                message=f"GitHub connection successful! {result.get('message', '')}",
            )
        else:
            return TestResult(
                success=False,
                message=result.get("error", "Connection failed. Check your token."),
            )
    except ImportError:
        return TestResult(
            success=False,
            message="GitHub Steampipe plugin is not available. "
                    "Ensure steampipe-plugin-github is installed.",
        )
    except Exception as e:
        logger.exception("GitHub connection test failed unexpectedly")
        return TestResult(
            success=False,
            message=f"Connection test failed: {str(e)[:200]}",
        )


def _extract_gitlab_error(resp: httpx.Response) -> str:
    """Extract a human-readable error description from a GitLab API error body."""
    try:
        data = resp.json()
    except Exception:
        return ""
    if isinstance(data, dict):
        desc = data.get("error_description") or data.get("message") or data.get("error")
        if isinstance(desc, str) and desc:
            return desc.strip()
    return ""


async def _test_gitlab_connection(cfg: dict) -> TestResult:
    """Actually validate GitLab credentials by calling the /api/v4/user endpoint."""
    baseurl = (cfg.get("baseurl", "") or cfg.get("base_url", "") or cfg.get("gitlab_url", "")).strip()
    gitlab_token = (cfg.get("token", "") or cfg.get("gitlab_token", "")).strip()

    if not baseurl or not gitlab_token:
        return TestResult(
            success=False,
            message="GitLab base URL and personal access token are required.",
        )

    # Normalise base URL: allow https://gitlab.com, https://gitlab.com/api/v4, etc.
    baseurl = baseurl.rstrip("/")
    if not baseurl.endswith("/api/v4"):
        baseurl = f"{baseurl}/api/v4"

    url = f"{baseurl}/user"
    headers = {
        "PRIVATE-TOKEN": gitlab_token,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            username = data.get("username", "") or "unknown"
            return TestResult(
                success=True,
                message=f"GitLab connection successful! Authenticated as '{username}'.",
            )
        elif resp.status_code == 401:
            return TestResult(
                success=False,
                message="GitLab authentication failed (401). "
                        "Check that your personal access token is valid and has not expired.",
            )
        elif resp.status_code == 403:
            detail = _extract_gitlab_error(resp)
            msg = "GitLab access denied (403). "
            if detail:
                msg += detail + " "
            msg += ("Your personal access token may lack the required permissions. "
                    "For fine-grained tokens, grant 'User: Read' (needed for the /user "
                    "endpoint) and 'read_api' for resource discovery.")
            return TestResult(success=False, message=msg)
        elif resp.status_code == 404:
            return TestResult(
                success=False,
                message="GitLab API endpoint not found (404). "
                        "Check that the base URL points to the GitLab API (e.g. https://gitlab.com/api/v4).",
            )
        else:
            return TestResult(
                success=False,
                message=f"GitLab API returned HTTP {resp.status_code}: {resp.text[:200]}",
            )
    except httpx.ConnectError:
        return TestResult(
            success=False,
            message=f"Could not connect to {baseurl}. "
                    "Check that the GitLab base URL is correct.",
        )
    except httpx.TimeoutException:
        return TestResult(
            success=False,
            message=f"Connection to {baseurl} timed out. "
                    "Check network connectivity and firewall rules.",
        )
    except Exception as e:
        logger.exception("GitLab connection test failed unexpectedly")
        return TestResult(
            success=False,
            message=f"Connection test failed: {str(e)[:200]}",
        )


async def _test_bitbucket_connection(cfg: dict) -> TestResult:
    """Validate Bitbucket credentials via the Bitbucket REST API."""
    base_url = (cfg.get("base_url", "") or "https://api.bitbucket.org/2.0").strip()
    username = cfg.get("username", "").strip()
    password = (cfg.get("password", "") or cfg.get("app_password", "")).strip()

    if not username or not password:
        return TestResult(
            success=False,
            message="Bitbucket email and API token are required.",
        )

    try:
        from app.services.steampipe_bitbucket import validate_bitbucket_connection
        result = validate_bitbucket_connection(
            username, password, base_url=base_url,
            workspace_slug=cfg.get("workspace_slug", ""),
        )
        if result.get("success"):
            return TestResult(
                success=True,
                message=f"Bitbucket connection successful! {result.get('message', '')}",
            )
        else:
            return TestResult(
                success=False,
                message=result.get("error", "Connection failed. Check your credentials."),
            )
    except ImportError:
        return TestResult(
            success=False,
            message="Bitbucket Steampipe plugin is not available. "
                    "Ensure steampipe-plugin-bitbucket is installed.",
        )
    except Exception as e:
        logger.exception("Bitbucket connection test failed unexpectedly")
        return TestResult(
            success=False,
            message=f"Connection test failed: {str(e)[:200]}",
        )


async def _test_slack_connection(cfg: dict) -> TestResult:
    """Validate Slack credentials via the Slack auth.test endpoint."""
    slack_token = (cfg.get("token", "") or cfg.get("slack_token", "")).strip()

    if not slack_token:
        return TestResult(
            success=False,
            message="Slack Bot Token is required.",
        )

    try:
        from app.services.steampipe_slack import validate_slack_connection
        result = validate_slack_connection(slack_token)
        if result.get("success"):
            return TestResult(
                success=True,
                message=f"Slack connection successful! {result.get('message', '')}",
            )
        else:
            return TestResult(
                success=False,
                message=result.get("error", "Connection failed. Check your token."),
            )
    except ImportError:
        return TestResult(
            success=False,
            message="Slack Steampipe plugin is not available. "
                    "Ensure steampipe-plugin-slack is installed.",
        )
    except Exception as e:
        logger.exception("Slack connection test failed unexpectedly")
        return TestResult(
            success=False,
            message=f"Connection test failed: {str(e)[:200]}",
        )


async def _test_microsoft365_connection(cfg: dict) -> TestResult:
    """Validate Microsoft 365 credentials via Microsoft Graph API."""
    tenant_id = cfg.get("tenant_id", "").strip()
    client_id = cfg.get("client_id", "").strip()
    client_secret = cfg.get("client_secret", "").strip()

    if not tenant_id or not client_id or not client_secret:
        return TestResult(
            success=False,
            message="Tenant ID, Client ID, and Client Secret are all required.",
        )

    try:
        from app.services.steampipe_microsoft365 import validate_microsoft365_connection
        result = validate_microsoft365_connection(tenant_id, client_id, client_secret)
        if result.get("success"):
            return TestResult(
                success=True,
                message=f"Microsoft 365 connection successful! {result.get('message', '')}",
            )
        else:
            return TestResult(
                success=False,
                message=result.get("error", "Connection failed. Check your credentials."),
            )
    except ImportError:
        return TestResult(
            success=False,
            message="Microsoft 365 Steampipe plugin is not available. "
                    "Ensure steampipe-plugin-microsoft365 is installed.",
        )
    except Exception as e:
        logger.exception("Microsoft 365 connection test failed unexpectedly")
        return TestResult(
            success=False,
            message=f"Connection test failed: {str(e)[:200]}",
        )


@router.post("/{provider}/setup")
async def setup_generic_integration(
    provider: str,
    body: GenericSetupRequest,
    current_user: CurrentUserDep,
):
    incoming_config = body.config

    # Load existing config to preserve unchanged secrets
    existing_config = load_config(current_user.organization_id, provider)

    # Determine secret fields: any incoming field whose value is the sentinel
    # or empty is treated as "keep existing". Since the frontend knows which
    # fields are password type, we check all incoming fields for sentinel values.
    secret_fields = [
        k for k, v in incoming_config.items()
        if not v or v == SECRET_SENTINEL
    ]
    merged = _merge_secret_fields(incoming_config, existing_config, secret_fields)

    save_config(current_user.organization_id, provider, merged)

    # Sync to dedicated config dir for known providers
    _sync_to_dedicated_config(provider, current_user.organization_id, merged)

    return {"success": True, "message": f"{provider.title()} configuration saved."}


@router.post("/{provider}/test", response_model=TestResult)
async def test_generic_connection(
    provider: str,
    current_user: CurrentUserDep,
):
    cfg = load_config(current_user.organization_id, provider)
    if not cfg:
        return TestResult(
            success=False,
            message=f"{provider.title()} is not configured yet. "
                    "Save your configuration first.",
        )

    # Provider-specific real connection tests
    if provider == "okta":
        return await _test_okta_connection(cfg)

    if provider == "github":
        return await _test_github_connection(cfg)

    if provider == "gitlab":
        return await _test_gitlab_connection(cfg)

    if provider == "microsoft365" or provider == "teams":
        return await _test_microsoft365_connection(cfg)

    if provider == "bitbucket":
        return await _test_bitbucket_connection(cfg)

    if provider == "slack":
        return await _test_slack_connection(cfg)

    # Default: just confirm config exists (no real test yet)
    return TestResult(
        success=True,
        message=f"{provider.title()} configuration found. "
                "Connection validation is not yet implemented for this service.",
    )


@router.get("/{provider}/config", response_model=GenericConfigResponse)
async def get_generic_config(
    provider: str,
    current_user: CurrentUserDep,
    secret_fields: str = Query(
        default="",
        description="Comma-separated list of field names to mask with sentinel",
    ),
):
    cfg = load_config(current_user.organization_id, provider)

    # Mask secret fields before returning
    if secret_fields:
        field_list = [f.strip() for f in secret_fields.split(",") if f.strip()]
        if field_list:
            cfg = _mask_secret_fields(cfg, field_list)

    return GenericConfigResponse(
        config=cfg,
        configured=bool(cfg),
    )
