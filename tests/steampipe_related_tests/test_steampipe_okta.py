import asyncio
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# The module to test
from app.services.steampipe_okta import (
    resolve_resource_id,
    extract_tags,
    run_query,
    _table_select_sql,
)
from app.mappers.canonical_map import OKTA_STEAMPIPE_TABLE_TO_TYPE, get_type


# ---------------------------------------------------------------------------
# Tests for the minimal inventory SELECT
# ---------------------------------------------------------------------------
class TestTableSelectSql:
    """Asset-inventory mode selects only the identifier column, not ``*``."""

    def test_default_selects_only_id(self):
        assert _table_select_sql("okta_user") == "select id from okta_user;"
        assert _table_select_sql("okta_group") == "select id from okta_group;"
        assert _table_select_sql("okta_application") == "select id from okta_application;"

    def test_group_owner_selects_fallback_column(self):
        assert _table_select_sql("okta_group_owner") == (
            "select group_id from okta_group_owner;"
        )


# ---------------------------------------------------------------------------
# Tests for canonical_map
# ---------------------------------------------------------------------------
class TestCanonicalMap:
    def test_all_okta_tables_have_mapping(self):
        """Every known Okta Steampipe table has a mapping in the YAML rules."""
        expected_tables = [
            "okta_app_assigned_group",
            "okta_app_assigned_user",
            "okta_application",
            "okta_auth_server",
            "okta_authenticator",
            "okta_authentication_policy",
            "okta_device",
            "okta_factor",
            "okta_group",
            "okta_group_owner",
            "okta_group_rule",
            "okta_idp_discovery_policy",
            "okta_mfa_policy",
            "okta_network_zone",
            "okta_password_policy",
            "okta_signon_policy",
            "okta_trusted_origin",
            "okta_user",
            "okta_user_type",
        ]
        for table in expected_tables:
            assert table in OKTA_STEAMPIPE_TABLE_TO_TYPE, f"Missing mapping for {table}"
            assert isinstance(OKTA_STEAMPIPE_TABLE_TO_TYPE[table], str), f"{table} not mapped to a string"

    def test_each_category_is_valid_canonical_type(self):
        """All mapped values are non-empty strings."""
        for table, ctype in OKTA_STEAMPIPE_TABLE_TO_TYPE.items():
            assert isinstance(ctype, str), f"{table} -> {ctype} is not a string"
            assert len(ctype) > 0, f"{table} -> empty string"

    def test_get_type_returns_correct_value(self):
        assert get_type("okta_user") == "Identity"
        assert get_type("okta_group") == "Group"
        assert get_type("okta_application") == "Application"
        assert get_type("okta_device") == "Device"

    def test_get_type_raises_on_unknown_table(self):
        with pytest.raises(KeyError):
            get_type("nonexistent_table")


# ---------------------------------------------------------------------------
# Tests for resource_id resolution
# ---------------------------------------------------------------------------
class TestResolveResourceId:
    def test_id_priority(self):
        row = {"id": "00u123", "name": "jane", "email": "jane@example.com"}
        assert resolve_resource_id(row) == "00u123"

    def test_name_fallback(self):
        row = {"name": "admin-group", "group_id": "00g456"}
        assert resolve_resource_id(row) == "admin-group"

    def test_group_id_fallback(self):
        row = {"group_id": "00g789", "owner_id": "00u999"}
        assert resolve_resource_id(row) == "00g789"

    def test_first_column_fallback(self):
        row = {"unknown_key": "fallback-value"}
        assert resolve_resource_id(row) == "fallback-value"

    def test_unknown_when_empty(self):
        assert resolve_resource_id({}) == "unknown"


# ---------------------------------------------------------------------------
# Tests for tag extraction
# ---------------------------------------------------------------------------
class TestExtractTags:
    def test_dict_tags(self):
        assert extract_tags({"tags": {"Env": "prod"}}) == {"Env": "prod"}

    def test_none_when_no_tags(self):
        assert extract_tags({"name": "foo"}) is None


# ---------------------------------------------------------------------------
# Tests for run_query
# ---------------------------------------------------------------------------
class TestRunQuery:
    def test_returns_rows_on_success(self):
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        mock_subprocess.stdout = json.dumps({"rows": [{"name": "test"}]})

        with patch("app.services.steampipe_okta.subprocess.run", return_value=mock_subprocess):
            result = run_query("select * from test;", "/tmp/steampipe", timeout_sec=30)
        assert result == [{"name": "test"}]

    def test_returns_empty_on_error(self):
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 1
        mock_subprocess.stderr = "error"

        with patch("app.services.steampipe_okta.subprocess.run", return_value=mock_subprocess):
            result = run_query("select * from test;", "/tmp/steampipe", timeout_sec=30)
        assert result == []


# ---------------------------------------------------------------------------
# Integration test for the full Steampipe import flow
# ---------------------------------------------------------------------------
def test_full_steampipe_import_flow():
    """Test that steampipe_okta produces resources with correct canonical_type."""
    from app.services.steampipe_okta import import_okta_resources_via_steampipe

    # Mock OKTA_STEAMPIPE_TABLE_TO_TYPE to only include the tables we want to test
    mock_mapping = {
        "okta_user": "Identity",
        "okta_group_owner": "Group",
    }

    # Mock Path.home() to return a path without .steampipe so symlinks are skipped
    mock_home = Path(tempfile.mkdtemp(prefix="steampipe_home_"))

    with (
        patch("app.services.steampipe_okta.OKTA_STEAMPIPE_TABLE_TO_TYPE", mock_mapping),
        patch("app.services.steampipe_okta.subprocess.Popen") as mock_popen,
        patch("pathlib.Path.home", return_value=mock_home),
    ):
        queries_run = []

        def fake_popen(cmd, **kwargs):
            proc = MagicMock()
            query = cmd[2] if len(cmd) > 2 else ""
            queries_run.append(query)

            if "okta_user" in query:
                out = json.dumps({
                    "rows": [
                        {"id": "00u123"},
                        # Null-id row must be skipped — no "unknown" asset.
                        {"id": None},
                    ]
                })
            elif "okta_group_owner" in query:
                # Inventory mode selects only the fallback id column.
                out = json.dumps({
                    "rows": [
                        {"group_id": "00g456"},
                        {"group_id": "00g789"},
                    ]
                })
            else:
                out = json.dumps({"rows": []})
            proc.communicate.return_value = (out, "")
            proc.returncode = 0
            return proc

        mock_popen.side_effect = fake_popen

        result = asyncio.run(import_okta_resources_via_steampipe(
            okta_domain="https://example.okta.com",
            okta_token="test-token",
        ))

        assert result["okta_domain"] == "example.okta.com"
        # The null-id user row is skipped, so still exactly 3 resources.
        assert result["resources_discovered"] == 3

        resources = result["resources_detail"]
        users = [r for r in resources if r["resource_type"] == "okta_user"]
        owners = [r for r in resources if r["resource_type"] == "okta_group_owner"]

        assert len(users) == 1
        assert users[0]["resource_id"] == "00u123"
        assert users[0]["resource_id"] != "unknown"
        assert users[0]["canonical_type"] == "Identity"
        assert users[0]["provider"] == "Okta"

        assert len(owners) == 2
        assert all(o["resource_id"] != "unknown" for o in owners)
        assert all(o["provider"] == "Okta" for o in owners)

        # Inventory mode: every query selects only the identifier column.
        assert queries_run
        assert all(q.startswith("select id from ") or q.startswith("select group_id from ") for q in queries_run)
        assert "select group_id from okta_group_owner;" in queries_run
        assert "select id from okta_user;" in queries_run
