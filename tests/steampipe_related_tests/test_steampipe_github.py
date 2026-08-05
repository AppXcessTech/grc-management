import asyncio
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from app.services.steampipe_github import (
    resolve_resource_id,
    extract_tags,
    run_query,
    _table_select_sql,
    _table_id_columns,
    TABLE_ID_COLUMN,
)
from app.mappers.canonical_map import GITHUB_STEAMPIPE_TABLE_TO_TYPE, get_type


# ---------------------------------------------------------------------------
# Tests for the minimal inventory SELECT
# ---------------------------------------------------------------------------
class TestTableSelectSql:
    """Asset-inventory mode selects only the identifier column(s), not ``*``."""

    def test_default_selects_only_id(self):
        assert _table_select_sql("github_team") == "select id from github_team;"
        assert _table_select_sql("github_repository") == "select id from github_repository;"

    def test_guid_identifier_with_login_extra(self):
        # guid is the identifier; user_login rides along for Identity dedup.
        assert _table_select_sql("github_organization_external_identity") == (
            "select guid, user_login from github_organization_external_identity;"
        )

    def test_identity_tables_select_login_for_dedup(self):
        assert _table_select_sql("github_user") == "select id, login from github_user;"
        assert _table_select_sql("github_organization_member") == (
            "select id, login from github_organization_member;"
        )
        assert _table_select_sql("github_team_member") == (
            "select id, login from github_team_member;"
        )

    def test_single_non_id_identifier(self):
        assert _table_select_sql("github_community_profile") == (
            "select repository_full_name from github_community_profile;"
        )
        assert _table_select_sql("github_repository_sbom") == (
            "select repository_full_name from github_repository_sbom;"
        )

    def test_composite_identifiers(self):
        assert _table_select_sql("github_actions_organization_variable") == (
            "select name, organization from github_actions_organization_variable;"
        )
        assert _table_select_sql("github_actions_repository_variable") == (
            "select name, repository_full_name from github_actions_repository_variable;"
        )
        assert _table_select_sql("github_code_owner") == (
            "select repository_full_name, line from github_code_owner;"
        )
        assert _table_select_sql("github_repository_collaborator") == (
            "select repository_full_name, user_login from github_repository_collaborator;"
        )
        assert _table_select_sql("github_actions_repository_secret") == (
            "select repository_full_name, name from github_actions_repository_secret;"
        )
        assert _table_select_sql("github_repository_vulnerability_alert") == (
            "select repository_full_name, number from github_repository_vulnerability_alert;"
        )

    def test_dependabot_alerts_namespaced_by_repo(self):
        assert _table_select_sql("github_repository_dependabot_alert") == (
            "select repository_full_name, alert_number from github_repository_dependabot_alert;"
        )
        assert _table_select_sql("github_organization_dependabot_alert") == (
            "select repository_full_name, alert_number from github_organization_dependabot_alert;"
        )

    def test_all_mapped_tables_have_an_identifier_spec(self):
        """Every GitHub table in the canonical map has an inventory id spec."""
        for table in GITHUB_STEAMPIPE_TABLE_TO_TYPE:
            assert table in TABLE_ID_COLUMN, f"Missing TABLE_ID_COLUMN entry for {table}"
            assert _table_id_columns(table), f"Empty id columns for {table}"


# ---------------------------------------------------------------------------
# Tests for resource_id resolution
# ---------------------------------------------------------------------------
class TestResolveResourceId:
    def test_single_id(self):
        assert resolve_resource_id({"id": "123"}, "github_team") == "123"

    def test_composite_join_with_colon(self):
        row = {"name": "MY_VAR", "organization": "acme"}
        assert resolve_resource_id(row, "github_actions_organization_variable") == "MY_VAR:acme"

    def test_composite_missing_part_falls_back(self):
        # Missing second part — falls back to legacy priority (name present).
        assert resolve_resource_id({"name": "MY_VAR"}, "github_actions_organization_variable") == "MY_VAR"

    def test_dependabot_namespaced(self):
        row = {"repository_full_name": "acme/app", "alert_number": 42}
        assert resolve_resource_id(row, "github_repository_dependabot_alert") == "acme/app:42"

    def test_guid(self):
        assert resolve_resource_id({"guid": "abc-123"}, "github_organization_external_identity") == "abc-123"

    def test_legacy_priority_fallback_without_table(self):
        row = {"node_id": "NODE1", "id": "42"}
        assert resolve_resource_id(row) == "NODE1"

    def test_unknown_when_empty(self):
        assert resolve_resource_id({}, "github_team") == "unknown"


# ---------------------------------------------------------------------------
# Tests for tag extraction
# ---------------------------------------------------------------------------
class TestExtractTags:
    def test_dict_tags(self):
        assert extract_tags({"tags": {"Env": "prod"}}) == {"Env": "prod"}

    def test_string_list_topics(self):
        assert extract_tags({"topics": ["security", "grc"]}) == [
            {"Key": "security", "Value": "security"},
            {"Key": "grc", "Value": "grc"},
        ]

    def test_none_when_no_tags(self):
        assert extract_tags({"name": "foo"}) is None


# ---------------------------------------------------------------------------
# Tests for run_query
# ---------------------------------------------------------------------------
class TestRunQuery:
    def test_returns_rows_on_success(self):
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        mock_subprocess.stdout = json.dumps({"rows": [{"id": "1"}]})

        with patch("app.services.steampipe_github.subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = (mock_subprocess.stdout, "")
            mock_popen.return_value.returncode = 0
            result = run_query("select id from github_team;", "/tmp/steampipe", timeout_sec=30)
        assert result == [{"id": "1"}]

    def test_returns_empty_on_error(self):
        with patch("app.services.steampipe_github.subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = ("", "error")
            mock_popen.return_value.returncode = 1
            result = run_query("select id from github_team;", "/tmp/steampipe", timeout_sec=30)
        assert result == []


# ---------------------------------------------------------------------------
# Integration test for the full Steampipe import flow
# ---------------------------------------------------------------------------
def test_full_steampipe_import_flow():
    """Test that steampipe_github produces resources with correct canonical_type."""
    from app.services.steampipe_github import import_github_resources_via_steampipe

    # Fine-grained tables only (no classic token in this test).
    mock_mapping = {
        "github_actions_artifact": "Artifact",
        "github_actions_organization_variable": "Configuration",
        "github_code_owner": "Policy",
        "github_team_member": "Group",
    }

    # Mock Path.home() so symlinks are skipped
    mock_home = Path(tempfile.mkdtemp(prefix="steampipe_home_"))

    with (
        patch("app.services.steampipe_github.GITHUB_STEAMPIPE_TABLE_TO_TYPE", mock_mapping),
        patch("app.services.steampipe_github.subprocess.Popen") as mock_popen,
        patch("pathlib.Path.home", return_value=mock_home),
    ):
        queries_run = []

        def fake_popen(cmd, **kwargs):
            proc = MagicMock()
            query = cmd[2] if len(cmd) > 2 else ""
            queries_run.append(query)

            if "github_my_repository" in query and "where" not in query:
                out = json.dumps({"rows": [
                    {"id": 1, "owner_login": "acme", "name_with_owner": "acme/app"},
                ]})
            elif "github_my_organization" in query:
                out = json.dumps({"rows": [
                    {"id": 1, "login": "acme"},
                ]})
            elif "github_team" in query:
                out = json.dumps({"rows": []})
            elif "github_actions_artifact" in query:
                out = json.dumps({"rows": [
                    {"id": 101},
                    # Null-id row must be skipped — no "unknown" asset.
                    {"id": None},
                ]})
            elif "github_actions_organization_variable" in query:
                out = json.dumps({"rows": [
                    {"name": "MY_VAR", "organization": "acme"},
                ]})
            elif "github_code_owner" in query:
                out = json.dumps({"rows": [
                    {"repository_full_name": "acme/app", "line": 7},
                ]})
            else:
                out = json.dumps({"rows": []})
            proc.communicate.return_value = (out, "")
            proc.returncode = 0
            return proc

        mock_popen.side_effect = fake_popen

        result = asyncio.run(import_github_resources_via_steampipe(
            github_token="ghp_test",
        ))

        assert result["account_id"] == "github"
        # artifact: 1 row (null-id skipped); org variable: 1; code owner: 1; team_member: 0.
        assert result["resources_discovered"] == 3

        resources = result["resources_detail"]
        by_type = {}
        for r in resources:
            by_type.setdefault(r["resource_type"], []).append(r)

        artifact = by_type["github_actions_artifact"][0]
        assert artifact["resource_id"] == "101"
        assert artifact["resource_id"] != "unknown"
        assert artifact["canonical_type"] == "Artifact"
        assert artifact["provider"] == "GitHub"

        variable = by_type["github_actions_organization_variable"][0]
        assert variable["resource_id"] == "MY_VAR:acme"
        assert variable["canonical_type"] == "Configuration"

        code_owner = by_type["github_code_owner"][0]
        assert code_owner["resource_id"] == "acme/app:7"
        assert code_owner["canonical_type"] == "Policy"

        # Inventory mode: never a bare `select * from github_...`.
        assert queries_run
        assert not any("select * from github_" in q for q in queries_run)
        # Composite identifiers are selected as their two columns.
        assert any("select name, organization from github_actions_organization_variable" in q for q in queries_run)
