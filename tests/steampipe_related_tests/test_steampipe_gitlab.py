import asyncio
import json
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

from app.services.steampipe_gitlab import (
    resolve_resource_id,
    extract_tags,
    run_query,
    _table_select_sql,
    _table_id_columns,
    TABLE_ID_COLUMN,
    TABLE_EXTRA_COLUMNS,
    FULL_SELECT_TABLES,
)
from app.mappers.canonical_map import GITLAB_STEAMPIPE_TABLE_TO_TYPE


# ---------------------------------------------------------------------------
# Tests for the minimal inventory SELECT
# ---------------------------------------------------------------------------
class TestTableSelectSql:
    """Asset-inventory mode selects only the identifier column(s), not ``*``."""

    def test_default_selects_only_id(self):
        assert _table_select_sql("gitlab_project") == "select id from gitlab_project;"
        assert _table_select_sql("gitlab_group") == "select id from gitlab_group;"
        assert _table_select_sql("gitlab_group_hook") == "select id from gitlab_group_hook;"

    def test_application_uses_application_id(self):
        assert _table_select_sql("gitlab_application") == (
            "select application_id from gitlab_application;"
        )

    def test_composite_identifiers(self):
        assert _table_select_sql("gitlab_group_variable") == (
            "select group_id, key, environment_scope from gitlab_group_variable;"
        )
        assert _table_select_sql("gitlab_project_variable") == (
            "select project_id, key, environment_scope from gitlab_project_variable;"
        )
        # Instance variables have no scope id — key + environment_scope.
        assert _table_select_sql("gitlab_instance_variable") == (
            "select key, environment_scope from gitlab_instance_variable;"
        )

    def test_extra_columns_ride_along(self):
        # Phase 3 needs project_id on pipeline rows; Identity dedup needs username.
        assert _table_select_sql("gitlab_project_pipeline") == (
            "select id, project_id, user_id from gitlab_project_pipeline;"
        )
        assert _table_select_sql("gitlab_user") == "select id, username from gitlab_user;"

    def test_full_select_tables(self):
        # gitlab_setting is a singleton with no id column — stays select *.
        assert _table_select_sql("gitlab_setting") == "select * from gitlab_setting;"

    def test_where_clause_is_appended(self):
        assert _table_select_sql("gitlab_group_variable", where="group_id = 7") == (
            "select group_id, key, environment_scope from gitlab_group_variable where group_id = 7;"
        )
        assert _table_select_sql("gitlab_user", where="id = 42") == (
            "select id, username from gitlab_user where id = 42;"
        )
        assert _table_select_sql("gitlab_setting", where="id = 1") == (
            "select * from gitlab_setting where id = 1;"
        )

    def test_all_mapped_tables_have_an_identifier_spec(self):
        """Every GitLab table in the canonical map has an inventory id spec."""
        for table in GITLAB_STEAMPIPE_TABLE_TO_TYPE:
            if table in FULL_SELECT_TABLES:
                continue
            assert table in TABLE_ID_COLUMN, f"Missing TABLE_ID_COLUMN entry for {table}"
            assert _table_id_columns(table), f"Empty id columns for {table}"


# ---------------------------------------------------------------------------
# Tests for resource_id resolution
# ---------------------------------------------------------------------------
class TestResolveResourceId:
    def test_single_id(self):
        assert resolve_resource_id({"id": "123"}, "gitlab_project") == "123"

    def test_application_id(self):
        assert resolve_resource_id({"application_id": "abc-123"}, "gitlab_application") == "abc-123"

    def test_composite_group_variable(self):
        row = {"group_id": 1, "key": "DEPLOY_TOKEN", "environment_scope": "production"}
        assert resolve_resource_id(row, "gitlab_group_variable") == "1:DEPLOY_TOKEN:production"

    def test_composite_project_variable(self):
        row = {"project_id": 9, "key": "AWS_KEY", "environment_scope": "*"}
        assert resolve_resource_id(row, "gitlab_project_variable") == "9:AWS_KEY:*"

    def test_composite_instance_variable(self):
        row = {"key": "GITLAB_TOKEN", "environment_scope": "*"}
        assert resolve_resource_id(row, "gitlab_instance_variable") == "GITLAB_TOKEN:*"

    def test_composite_missing_part_falls_back(self):
        # Missing environment_scope — falls back to legacy priority (key present).
        assert resolve_resource_id({"group_id": 1, "key": "DEPLOY"}, "gitlab_group_variable") == "DEPLOY"

    def test_setting_constant(self):
        assert resolve_resource_id({}, "gitlab_setting") == "instance"
        assert resolve_resource_id({"title": "whatever"}, "gitlab_setting") == "instance"

    def test_legacy_priority_fallback_without_table(self):
        row = {"web_url": "https://gitlab.com/acme/app", "id": "42"}
        assert resolve_resource_id(row) == "https://gitlab.com/acme/app"

    def test_unknown_when_empty(self):
        assert resolve_resource_id({}, "gitlab_project") == "unknown"


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

        with patch("app.services.steampipe_gitlab.subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = (mock_subprocess.stdout, "")
            mock_popen.return_value.returncode = 0
            result = run_query("select id from gitlab_project;", "/tmp/steampipe", timeout_sec=30)
        assert result == [{"id": "1"}]

    def test_returns_empty_on_error(self):
        with patch("app.services.steampipe_gitlab.subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = ("", "error")
            mock_popen.return_value.returncode = 1
            result = run_query("select id from gitlab_project;", "/tmp/steampipe", timeout_sec=30)
        assert result == []


# ---------------------------------------------------------------------------
# Integration test for the full Steampipe import flow
# ---------------------------------------------------------------------------
def test_full_steampipe_import_flow():
    """Test that steampipe_gitlab produces resources with correct ids/types."""
    from app.services.steampipe_gitlab import import_gitlab_resources_via_steampipe

    mock_mapping = {
        "gitlab_group_variable": "Configuration",
        "gitlab_project": "Repository",
        "gitlab_my_project": "Repository",
        "gitlab_group": "Group",
        "gitlab_user": "Identity",
        "gitlab_project_pipeline": "Pipeline",
    }

    # Mock Path.home() so symlinks are skipped
    mock_home = Path(tempfile.mkdtemp(prefix="steampipe_home_"))

    with (
        patch("app.services.steampipe_gitlab.GITLAB_STEAMPIPE_TABLE_TO_TYPE", mock_mapping),
        patch("app.services.steampipe_gitlab.subprocess.Popen") as mock_popen,
        patch("pathlib.Path.home", return_value=mock_home),
    ):
        queries_run = []

        def fake_popen(cmd, **kwargs):
            proc = MagicMock()
            query = cmd[2] if len(cmd) > 2 else ""
            queries_run.append(query)

            if "gitlab_my_project" in query:
                out = json.dumps({"rows": [{"id": 101, "full_path": "acme/app"}]})
            elif "gitlab_group" in query:
                out = json.dumps({"rows": [{"id": 5, "full_path": "acme"}]})
            elif "gitlab_project" in query and "where" in query:
                out = json.dumps({"rows": [{"id": 101}]})
            elif "gitlab_group_variable" in query:
                out = json.dumps({"rows": [
                    {"group_id": 5, "key": "DEPLOY", "environment_scope": "production"},
                    # Null key must not produce an asset with a broken id.
                    {"group_id": 5, "key": None, "environment_scope": "production"},
                ]})
            elif "gitlab_project_pipeline" in query:
                out = json.dumps({"rows": [{"id": 77, "project_id": 101, "user_id": 3}]})
            elif "gitlab_user" in query:
                out = json.dumps({"rows": [{"id": 3, "username": "alice"}]})
            else:
                out = json.dumps({"rows": []})
            proc.communicate.return_value = (out, "")
            proc.returncode = 0
            return proc

        mock_popen.side_effect = fake_popen

        result = asyncio.run(import_gitlab_resources_via_steampipe(
            baseurl="https://gitlab.com/api/v4",
            token="glpat_test",
        ))

        assert result["resources_discovered"] >= 1

        resources = result["resources_detail"]
        by_type = {}
        for r in resources:
            by_type.setdefault(r["resource_type"], []).append(r)

        variable = by_type["gitlab_group_variable"][0]
        assert variable["resource_id"] == "5:DEPLOY:production"
        assert variable["canonical_type"] == "Configuration"
        assert variable["provider"] == "GitLab"

        project = by_type["gitlab_project"][0]
        assert project["resource_id"] == "101"
        assert project["canonical_type"] == "Repository"

        user = by_type["gitlab_user"][0]
        assert user["resource_id"] == "3"
        assert user["canonical_type"] == "Identity"

        # Inventory mode: no bare `select * from gitlab_...` (except gitlab_setting).
        assert queries_run
        assert not any("select * from gitlab_" in q for q in queries_run)
        # Composite identifiers are selected as their columns + qualifier kept.
        assert any(
            "select group_id, key, environment_scope from gitlab_group_variable where group_id = 5"
            in q for q in queries_run
        )
        # Phase 3 user resolution happens with a minimal id select.
        assert any("select id, username from gitlab_user where id = 3" in q for q in queries_run)
