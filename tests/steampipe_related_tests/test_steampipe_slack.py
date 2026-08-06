import asyncio
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from app.services.steampipe_slack import (
    resolve_resource_id,
    extract_tags,
    run_query,
    _table_select_sql,
)
from app.mappers.canonical_map import SLACK_STEAMPIPE_TABLE_TO_TYPE, get_type


# ---------------------------------------------------------------------------
# Tests for the minimal inventory SELECT
# ---------------------------------------------------------------------------
class TestTableSelectSql:
    """Asset-inventory mode selects only the identifier column(s), not ``*``."""

    def test_selects_identifier_and_extras(self):
        assert _table_select_sql("slack_user") == "select id, email from slack_user;"
        assert _table_select_sql("slack_conversation") == "select id, name from slack_conversation;"
        assert _table_select_sql("slack_group") == "select id, name from slack_group;"
        assert _table_select_sql("slack_connection") == "select team_id, team, workspace_domain from slack_connection;"

    def test_composite_identifier_tables(self):
        assert _table_select_sql("slack_conversation_member") == (
            "select conversation_id, member_id from slack_conversation_member;"
        )
        assert _table_select_sql("slack_access_log") == (
            "select user_id, date_first, user_name from slack_access_log;"
        )


# ---------------------------------------------------------------------------
# Tests for canonical_map
# ---------------------------------------------------------------------------
class TestCanonicalMap:
    def test_all_slack_tables_have_mapping(self):
        """Every known Slack Steampipe table has a mapping in the YAML rules."""
        expected_tables = [
            "slack_access_log",
            "slack_connection",
            "slack_conversation",
            "slack_conversation_member",
            "slack_group",
            "slack_user",
        ]
        for table in expected_tables:
            assert table in SLACK_STEAMPIPE_TABLE_TO_TYPE, f"Missing mapping for {table}"
            assert isinstance(SLACK_STEAMPIPE_TABLE_TO_TYPE[table], str), f"{table} not mapped to a string"

    def test_each_category_is_valid_canonical_type(self):
        for table, ctype in SLACK_STEAMPIPE_TABLE_TO_TYPE.items():
            assert isinstance(ctype, str), f"{table} -> {ctype} is not a string"
            assert len(ctype) > 0, f"{table} -> empty string"

    def test_get_type_returns_correct_value(self):
        assert get_type("slack_user") == "Identity"
        assert get_type("slack_conversation") == "Group"
        assert get_type("slack_access_log") == "Logging"
        assert get_type("slack_connection") == "Organization"

    def test_get_type_raises_on_unknown_table(self):
        try:
            get_type("nonexistent_table")
            assert False, "expected KeyError"
        except KeyError:
            pass


# ---------------------------------------------------------------------------
# Tests for resource_id resolution
# ---------------------------------------------------------------------------
class TestResolveResourceId:
    def test_user_uses_id_only(self):
        row = {"id": "U0K7FH41E", "email": "jim@example.com"}
        assert resolve_resource_id(row, "slack_user") == "U0K7FH41E"

    def test_conversation_member_composite(self):
        row = {"conversation_id": "C02GC4A7Q", "member_id": "U0K7FH41E"}
        assert resolve_resource_id(row, "slack_conversation_member") == "C02GC4A7Q:U0K7FH41E"

    def test_access_log_composite(self):
        row = {"user_id": "U0K7FH41E", "user_name": "jim", "date_first": 1710000000}
        assert resolve_resource_id(row, "slack_access_log") == "U0K7FH41E:1710000000"

    def test_missing_composite_part_falls_back(self):
        row = {"conversation_id": "C02GC4A7Q"}
        assert resolve_resource_id(row, "slack_conversation_member") == "C02GC4A7Q"

    def test_connection_uses_team_id(self):
        row = {"team_id": "T0BMPN6CLGL", "team": "cyall", "workspace_domain": "cyall"}
        assert resolve_resource_id(row, "slack_connection") == "T0BMPN6CLGL"

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
        proc = MagicMock()
        proc.returncode = 0
        proc.communicate.return_value = (json.dumps({"rows": [{"id": "U0A"}]}), "")

        with patch("app.services.steampipe_slack.subprocess.Popen", return_value=proc):
            rows, err = run_query("select id from slack_user;", "/tmp/steampipe", timeout_sec=30)
        assert rows == [{"id": "U0A"}]
        assert err == ""

    def test_returns_error_on_failure(self):
        proc = MagicMock()
        proc.returncode = 1
        proc.communicate.return_value = ("", "Error: slack: missing_scope (SQLSTATE HV000)")

        with patch("app.services.steampipe_slack.subprocess.Popen", return_value=proc):
            rows, err = run_query("select id from slack_conversation;", "/tmp/steampipe", timeout_sec=30)
        assert rows == []
        assert "missing_scope" in err


# ---------------------------------------------------------------------------
# Integration test for the full Steampipe import flow
# ---------------------------------------------------------------------------
def test_full_steampipe_import_flow():
    """Test that steampipe_slack produces resources with correct canonical_type."""
    from app.services.steampipe_slack import import_slack_resources_via_steampipe

    # Mock the table map to a small known set so the test is self-contained.
    mock_mapping = {
        "slack_user": "Identity",
        "slack_conversation": "Group",
        "slack_conversation_member": "Group",
    }

    mock_home = Path(tempfile.mkdtemp(prefix="steampipe_home_"))

    with (
        patch("app.services.steampipe_slack.SLACK_STEAMPIPE_TABLE_TO_TYPE", mock_mapping),
        patch("app.services.steampipe_slack.subprocess.Popen") as mock_popen,
        patch("pathlib.Path.home", return_value=mock_home),
    ):
        queries_run = []

        def fake_popen(cmd, **kwargs):
            proc = MagicMock()
            query = cmd[2] if len(cmd) > 2 else ""
            queries_run.append(query)

            if "slack_conversation" in query and "conversation_member" not in query:
                out = json.dumps({"rows": [{"id": "C02GC4A7Q", "name": "general"}]})
            elif "slack_user" in query:
                out = json.dumps({
                    "rows": [
                        {"id": "U0K7FH41E", "email": "jim@example.com"},
                        # Null-email row must still resolve by id only.
                        {"id": "U0BOT", "email": None},
                    ]
                })
            elif "slack_conversation_member" in query:
                out = json.dumps({
                    "rows": [
                        {"conversation_id": "C02GC4A7Q", "member_id": "U0K7FH41E"},
                    ]
                })
            else:
                out = json.dumps({"rows": []})
            proc.communicate.return_value = (out, "")
            proc.returncode = 0
            return proc

        mock_popen.side_effect = fake_popen

        result = asyncio.run(import_slack_resources_via_steampipe(
            slack_token="xoxb-test-token",
            workspace="acme-workspace",
        ))

        assert result["account_id"] == "acme-workspace"
        # 2 users + 1 conversation + 1 member (from the qualifier query).
        assert result["resources_discovered"] == 4

        resources = result["resources_detail"]
        users = [r for r in resources if r["resource_type"] == "slack_user"]
        conversations = [r for r in resources if r["resource_type"] == "slack_conversation"]
        members = [r for r in resources if r["resource_type"] == "slack_conversation_member"]

        assert len(users) == 2
        assert all(u["resource_id"] != "unknown" for u in users)
        assert all(u["provider"] == "Slack" for u in users)
        assert users[0]["resource_id"] == "U0K7FH41E"
        assert users[0]["canonical_type"] == "Identity"
        assert users[0]["details"]["workspace_domain"] == "acme-workspace"

        assert len(conversations) == 1
        assert conversations[0]["resource_id"] == "C02GC4A7Q"

        # conversation_member requires a conversation_id qualifier.
        assert len(members) == 1
        assert members[0]["resource_id"] == "C02GC4A7Q:U0K7FH41E"
        assert any("where conversation_id = 'C02GC4A7Q'" in q for q in queries_run)

        # Inventory mode: no bare `select *` queries.
        assert all(not q.lower().startswith("select *") for q in queries_run)
