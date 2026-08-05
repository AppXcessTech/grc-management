"""Tests for Bitbucket workspace-scoped discovery and API-token validation.

Covers:
  - ``_gather_context`` using the workspace-scoped Steampipe tables
    (bitbucket_workspace / bitbucket_project) plus REST API repository
    enumeration (bitbucket_my_* is deprecated — 410 Gone).
  - ``validate_bitbucket_connection`` API-token era messages (401) and the
    required workspace verification (success / 404 / missing slug).
  - Inventory-mode minimal ``uuid`` selects (asset inventory: id + provider).
"""
import asyncio
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

import pytest

from app.services import steampipe_bitbucket as sb
from app.mappers.canonical_map import BITBUCKET_STEAMPIPE_TABLE_TO_TYPE


class FakeResponse:
    def __init__(self, status_code: int, json_data=None, text: str = ""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text

    def json(self):
        return self._json


def _canned_run_query(sql: str, install_dir: str, timeout_sec: int = 0):
    if "bitbucket_workspace" in sql and "workspace_slug" not in sql:
        return [{"uuid": "{ws-1}", "slug": "acme", "name": "Acme"}]
    if "bitbucket_project" in sql:
        return [{"uuid": "{proj-1}", "workspace_slug": "acme", "key": "P1", "name": "Acme Projects"}]
    return []


def _canned_repos(base_url, username, app_password, workspace_slug):
    return [
        {"full_name": "acme/repo1", "name": "repo1", "workspace_slug": "acme"},
        {"full_name": "acme/repo2", "name": "repo2", "workspace_slug": "acme"},
    ]


# ---------------------------------------------------------------------------
# Tests for the minimal inventory SELECT
# ---------------------------------------------------------------------------
class TestTableSelectSql:
    """Asset-inventory mode selects only the identifier column, not ``*``."""

    def test_default_selects_only_uuid(self):
        assert sb._table_select_sql("bitbucket_workspace") == "select uuid from bitbucket_workspace;"
        assert sb._table_select_sql("bitbucket_project") == "select uuid from bitbucket_project;"
        assert sb._table_select_sql("bitbucket_repository") == "select uuid from bitbucket_repository;"
        assert sb._table_select_sql("bitbucket_workspace_member") == "select uuid from bitbucket_workspace_member;"

    def test_branch_restriction_uses_id(self):
        # The YAML rule resolves $.id for branch restrictions (no uuid).
        assert sb._table_select_sql("bitbucket_branch_restriction") == (
            "select id from bitbucket_branch_restriction;"
        )

    def test_my_tables_map_to_uuid(self):
        assert sb._table_select_sql("bitbucket_my_workspace") == "select uuid from bitbucket_my_workspace;"
        assert sb._table_select_sql("bitbucket_my_project") == "select uuid from bitbucket_my_project;"
        assert sb._table_select_sql("bitbucket_my_repository") == "select uuid from bitbucket_my_repository;"

    def test_all_mapped_tables_have_an_identifier(self):
        """Every Bitbucket table in the canonical map has an id column spec."""
        for table in BITBUCKET_STEAMPIPE_TABLE_TO_TYPE:
            assert sb._table_id_column(table), f"Empty id column for {table}"


# ---------------------------------------------------------------------------
# Tests for resource_id resolution
# ---------------------------------------------------------------------------
class TestResolveResourceId:
    def test_uuid_priority(self):
        row = {"uuid": "{abc-123}", "full_name": "acme/repo1", "slug": "repo1"}
        assert sb.resolve_resource_id(row, "bitbucket_repository") == "{abc-123}"

    def test_table_id_column_used(self):
        assert sb.resolve_resource_id({"uuid": "{u}", "id": 99}, "bitbucket_branch_restriction") == "99"

    def test_legacy_fallback_without_table(self):
        row = {"full_name": "acme/repo1"}
        assert sb.resolve_resource_id(row) == "acme/repo1"

    def test_unknown_when_empty(self):
        assert sb.resolve_resource_id({}, "bitbucket_workspace") == "unknown"

    def test_row_to_entry_returns_none_without_id(self):
        assert sb._row_to_entry({"uuid": None}, "bitbucket_workspace", "Organization") is None
        assert sb._row_to_entry({}, "bitbucket_workspace", "Organization") is None


class TestWorkspaceScoping:
    def test_scope_uses_configured_slug(self, monkeypatch):
        monkeypatch.setattr(sb, "run_query", _canned_run_query)
        monkeypatch.setattr(sb, "_list_workspace_repositories_via_api", _canned_repos)
        ctx = sb._gather_context(
            "/tmp/steampipe",
            workspace_slug="acme",
            base_url="https://api.bitbucket.org/2.0",
            username="ada@example.com",
            app_password="valid-token",
        )
        assert ctx["workspace_slugs"] == {"acme"}
        assert ctx["full_names"] == {"acme/repo1", "acme/repo2"}
        assert len(ctx["workspaces"]) == 1 and ctx["workspaces"][0]["slug"] == "acme"
        assert all(p["workspace_slug"] == "acme" for p in ctx["projects"])
        assert ctx["warnings"] == []

    def test_missing_slug_emits_warning(self, monkeypatch):
        monkeypatch.setattr(sb, "run_query", _canned_run_query)
        monkeypatch.setattr(sb, "_list_workspace_repositories_via_api", _canned_repos)
        ctx = sb._gather_context("/tmp/steampipe")
        assert ctx["workspace_slugs"] == set()
        assert ctx["full_names"] == set()
        assert any(w.get("action") == "Config" for w in ctx["warnings"])

    def test_unknown_slug_emits_scope_warning(self, monkeypatch):
        monkeypatch.setattr(sb, "run_query", lambda *a, **k: [])
        monkeypatch.setattr(sb, "_list_workspace_repositories_via_api", lambda *a, **k: [])
        ctx = sb._gather_context(
            "/tmp/steampipe",
            workspace_slug="nope",
            base_url="https://api.bitbucket.org/2.0",
            username="ada@example.com",
            app_password="valid-token",
        )
        assert ctx["workspace_slugs"] == set()
        assert ctx["full_names"] == set()
        assert any(w.get("action") == "Scope" for w in ctx["warnings"])


class TestValidateConnection:
    def test_401_message_guides_to_api_token(self, monkeypatch):
        fake = MagicMock()
        fake.get.return_value = FakeResponse(401, text="Authentication problem")
        fake.__enter__ = MagicMock(return_value=fake)
        fake.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(sb.httpx, "Client", lambda **kw: fake)

        result = sb.validate_bitbucket_connection(
            "user@example.com", "wrong-token", workspace_slug="acme",
        )
        assert result["success"] is False
        assert "401" in result["error"]
        assert "API token" in result["error"]
        assert "July 28, 2026" in result["error"]

    def test_success_with_workspace_slug(self, monkeypatch):
        fake = MagicMock()
        fake.get.side_effect = [
            FakeResponse(200, {"display_name": "Ada Lovelace", "username": "ada"}),
            FakeResponse(200, {"name": "Acme Corp"}),
        ]
        fake.__enter__ = MagicMock(return_value=fake)
        fake.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(sb.httpx, "Client", lambda **kw: fake)

        result = sb.validate_bitbucket_connection(
            "ada@example.com", "valid-token", workspace_slug="acme",
        )
        assert result["success"] is True
        assert "Ada Lovelace" in result["message"]
        assert "Acme Corp" in result["message"]

    def test_workspace_not_found(self, monkeypatch):
        fake = MagicMock()
        fake.get.side_effect = [
            FakeResponse(200, {"display_name": "Ada Lovelace"}),
            FakeResponse(404),
        ]
        fake.__enter__ = MagicMock(return_value=fake)
        fake.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(sb.httpx, "Client", lambda **kw: fake)

        result = sb.validate_bitbucket_connection(
            "ada@example.com", "valid-token", workspace_slug="ghost",
        )
        assert result["success"] is False
        assert "ghost" in result["error"]

    def test_missing_workspace_slug_required(self, monkeypatch):
        fake = MagicMock()
        fake.get.return_value = FakeResponse(200, {"display_name": "Ada Lovelace"})
        fake.__enter__ = MagicMock(return_value=fake)
        fake.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(sb.httpx, "Client", lambda **kw: fake)

        result = sb.validate_bitbucket_connection("ada@example.com", "valid-token")
        assert result["success"] is False
        assert "workspace slug" in result["error"].lower()
        # No API calls should have been made
        assert fake.get.call_count == 0


# ---------------------------------------------------------------------------
# Integration test for the full Steampipe import flow
# ---------------------------------------------------------------------------
def test_full_steampipe_import_flow():
    """Test that steampipe_bitbucket produces resources with id + provider."""
    from app.services.steampipe_bitbucket import import_bitbucket_resources_via_steampipe

    # Mock the mapping to a small subset (uuid-id tables + branch restriction).
    mock_mapping = {
        "bitbucket_workspace": "Organization",
        "bitbucket_project": "Application",
        "bitbucket_repository": "Repository",
        "bitbucket_branch_restriction": "Repository",
    }

    mock_home = Path(tempfile.mkdtemp(prefix="steampipe_home_"))

    with (
        patch("app.services.steampipe_bitbucket.BITBUCKET_STEAMPIPE_TABLE_TO_TYPE", mock_mapping),
        patch("app.services.steampipe_bitbucket.subprocess.Popen") as mock_popen,
        patch("app.services.steampipe_bitbucket._list_workspace_repositories_via_api") as mock_repos,
        patch("pathlib.Path.home", return_value=mock_home),
    ):
        mock_repos.return_value = [{"full_name": "acme/repo1"}]

        queries_run = []

        def fake_popen(cmd, **kwargs):
            proc = MagicMock()
            query = cmd[2] if len(cmd) > 2 else ""
            queries_run.append(query)

            if "bitbucket_workspace" in query:
                # Context query: SELECT uuid FROM bitbucket_workspace WHERE slug = ...
                out = json.dumps({"rows": [{"uuid": "{ws-1}"}]})
            elif "bitbucket_project" in query:
                out = json.dumps({"rows": [{"uuid": "{proj-1}"}]})
            elif "bitbucket_repository" in query:
                out = json.dumps({"rows": [
                    {"uuid": "{repo-1}"},
                    # Null-uuid row must be skipped.
                    {"uuid": None},
                ]})
            elif "bitbucket_branch_restriction" in query:
                out = json.dumps({"rows": [{"id": 42}]})
            else:
                out = json.dumps({"rows": []})
            proc.communicate.return_value = (out, "")
            proc.returncode = 0
            return proc

        mock_popen.side_effect = fake_popen

        result = asyncio.run(import_bitbucket_resources_via_steampipe(
            base_url="https://api.bitbucket.org/2.0",
            username="ada@example.com",
            app_password="valid-token",
            workspace_slug="acme",
        ))

        # workspace (1) + project (1) + repository (1, null-uuid skipped) +
        # branch_restriction (1) = 4.
        assert result["resources_discovered"] == 4
        assert result["account_id"] == "https://api.bitbucket.org/2.0"

        resources = result["resources_detail"]
        by_type = {}
        for r in resources:
            by_type.setdefault(r["resource_type"], []).append(r)

        assert by_type["bitbucket_repository"][0]["resource_id"] == "{repo-1}"
        assert by_type["bitbucket_repository"][0]["resource_id"] != "unknown"
        assert by_type["bitbucket_repository"][0]["provider"] == "Bitbucket"
        assert by_type["bitbucket_repository"][0]["canonical_type"] == "Repository"

        # Branch restrictions use their numeric id (not uuid).
        assert by_type["bitbucket_branch_restriction"][0]["resource_id"] == "42"

        # Inventory mode: never a bare `select * from bitbucket_`.
        assert queries_run
        assert not any("select * from bitbucket_" in q for q in queries_run)
        assert any("select uuid from bitbucket_repository" in q for q in queries_run)
        assert any("select id from bitbucket_branch_restriction" in q for q in queries_run)
