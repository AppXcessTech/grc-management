import asyncio
import pytest
import subprocess
import tempfile
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

# The module to test
from app.services.steampipe_aws import (
    resolve_resource_id,
    extract_tags,
    run_query,
    _table_select_sql,
)
from app.services.ingestion import (
    _build_from_rule,
    _resolve_status,
)
from app.mappers.canonical_map import STEAMPIPE_TABLE_TO_TYPE, get_type


# ---------------------------------------------------------------------------
# Tests for the minimal inventory SELECT
# ---------------------------------------------------------------------------
class TestTableSelectSql:
    """Asset-inventory mode selects only the identifier column, not ``*``."""

    def test_default_selects_only_arn(self):
        assert _table_select_sql("aws_s3_bucket") == "select arn from aws_s3_bucket;"
        assert _table_select_sql("aws_ec2_instance") == "select arn from aws_ec2_instance;"

    def test_arn_less_tables_select_fallback_column(self):
        assert _table_select_sql("aws_iam_account_password_policy") == (
            "select account_id from aws_iam_account_password_policy;"
        )
        assert _table_select_sql("aws_iam_credential_report") == (
            "select user_arn from aws_iam_credential_report;"
        )
        assert _table_select_sql("aws_identitystore_user") == (
            "select name from aws_identitystore_user;"
        )
        assert _table_select_sql("aws_ecr_image_scan_finding") == (
            "select name from aws_ecr_image_scan_finding;"
        )
        assert _table_select_sql("aws_vpc_flow_log") == (
            "select flow_log_id from aws_vpc_flow_log;"
        )


# ---------------------------------------------------------------------------
# Tests for canonical_map
# ---------------------------------------------------------------------------
class TestCanonicalMap:
    def test_all_tables_have_mapping(self):
        """Every known Steampipe table has a mapping in the YAML rules."""
        expected_tables = [
            "aws_accessanalyzer_analyzer",
            "aws_accessanalyzer_finding",
            "aws_acm_certificate",
            "aws_cloudtrail_trail",
            "aws_cloudwatch_alarm",
            "aws_cloudwatch_log_group",
            "aws_codecommit_repository",
            "aws_config_configuration_recorder",
            "aws_docdb_cluster",
            "aws_dynamodb_table",
            "aws_ebs_volume",
            "aws_ec2_application_load_balancer",
            "aws_ec2_autoscaling_group",
            "aws_ec2_classic_load_balancer",
            "aws_ec2_instance",
            "aws_ec2_network_load_balancer",
            "aws_ecr_image_scan_finding",
            "aws_ecr_repository",
            "aws_ecs_cluster",
            "aws_ecs_service",
            "aws_ecs_task",
            "aws_efs_file_system",
            "aws_eks_cluster",
            "aws_eks_node_group",
            "aws_guardduty_detector",
            "aws_guardduty_finding",
            "aws_iam_account_password_policy",
            "aws_iam_credential_report",
            "aws_iam_group",
            "aws_iam_policy",
            "aws_iam_role",
            "aws_iam_user",
            "aws_identitystore_user",
            "aws_inspector2_finding",
            "aws_kms_key",
            "aws_lambda_function",
            "aws_organizations_account",
            "aws_rds_db_instance",
            "aws_redshift_cluster",
            "aws_s3_bucket",
            "aws_securityhub_finding",
            "aws_securityhub_hub",
            "aws_sqs_queue",
            "aws_vpc",
            "aws_vpc_flow_log",
            "aws_vpc_network_acl",
            "aws_vpc_route_table",
            "aws_vpc_security_group",
            "aws_vpc_subnet",
        ]
        for table in expected_tables:
            assert table in STEAMPIPE_TABLE_TO_TYPE, f"Missing mapping for {table}"
            assert isinstance(STEAMPIPE_TABLE_TO_TYPE[table], str), f"{table} not mapped to a string"

    def test_each_category_is_valid_canonical_type(self):
        """All mapped values are non-empty strings."""
        for table, ctype in STEAMPIPE_TABLE_TO_TYPE.items():
            assert isinstance(ctype, str), f"{table} -> {ctype} is not a string"
            assert len(ctype) > 0, f"{table} -> empty string"

    def test_get_type_returns_correct_value(self):
        assert get_type("aws_s3_bucket") == "Storage"
        assert get_type("aws_ec2_instance") == "Compute"
        assert get_type("aws_vpc_security_group") == "Firewall"
        assert get_type("aws_sqs_queue") == "Application"

    def test_get_type_raises_on_unknown_table(self):
        with pytest.raises(KeyError):
            get_type("nonexistent_table")


# ---------------------------------------------------------------------------
# Tests for resource_id resolution
# ---------------------------------------------------------------------------
class TestResolveResourceId:
    def test_arn_priority(self):
        row = {"arn": "arn:aws:s3:::my-bucket", "name": "my-bucket", "id": "bucket-id"}
        assert resolve_resource_id(row) == "arn:aws:s3:::my-bucket"

    def test_name_fallback(self):
        row = {"name": "my-instance", "instance_id": "i-1234"}
        assert resolve_resource_id(row) == "my-instance"

    def test_instance_id_fallback(self):
        row = {"instance_id": "i-1234"}
        assert resolve_resource_id(row) == "i-1234"

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

    def test_list_tags_with_key_value(self):
        row = {"Tags": [{"Key": "Name", "Value": "my-resource"}, {"Key": "Env", "Value": "prod"}]}
        result = extract_tags(row)
        assert result == [{"Key": "Name", "Value": "my-resource"}, {"Key": "Env", "Value": "prod"}]

    def test_none_when_no_tags(self):
        assert extract_tags({"name": "foo"}) is None


# ---------------------------------------------------------------------------
# Tests for _build_from_rule (YAML-driven ingestion)
# ---------------------------------------------------------------------------
class TestBuildFromRule:
    def test_builds_asset_data(self):
        now = datetime.now()
        resource = {
            "resource_type": "aws_s3_bucket",
            "resource_id": "my-bucket",
            "canonical_type": "Storage",
            "display_name": "my-bucket",
            "account_id": "123456789012",
            "region": "us-east-1",
            # The raw Steampipe row goes in details — this is what the
            # YAML rules engine resolves mappings against
            "details": {
                "name": "my-bucket",
                "arn": "arn:aws:s3:::my-bucket",
                "account_id": "123456789012",
                "region": "us-east-1",
            },
            "tags": {"Env": "prod"},
        }
        asset, rels = _build_from_rule(organization_id=1, resource=resource, now=now)
        assert asset is not None
        assert asset.canonical_type == "Storage"
        assert asset.display_name is not None
        assert asset.account_id == "123456789012"
        assert asset.region == "us-east-1"
        assert asset.tags == {"Env": "prod"}

    def test_builds_relationships(self):
        now = datetime.now()
        resource = {
            "resource_type": "aws_ec2_instance",
            "resource_id": "i-1234",
            "canonical_type": "Compute",
            "display_name": "my-instance",
            "relationships": {
                "VPC": "vpc-abc",
                "Subnet": "subnet-xyz",
                "SecurityGroup": ["sg-111", "sg-222"],
            },
            "details": {"instance_id": "i-1234", "arn": "arn:aws:ec2:us-east-1:123:instance/i-1234"},
        }
        asset, rels = _build_from_rule(organization_id=1, resource=resource, now=now)
        assert asset is not None
        assert len(rels) == 4  # VPC (1) + Subnet (1) + SecurityGroup (2) = 4

        rel_by_type = {r.target_provider_resource_id: r.relationship_type for r in rels}
        assert rel_by_type["vpc-abc"] == "belongs_to"
        assert rel_by_type["subnet-xyz"] == "belongs_to"
        assert rel_by_type["sg-111"] == "associated_with"
        assert rel_by_type["sg-222"] == "associated_with"

    def test_returns_none_when_no_resource_type(self):
        now = datetime.now()
        asset, rels = _build_from_rule(organization_id=1, resource={"resource_id": "x"}, now=now)
        assert asset is None
        assert rels == []

    def test_returns_none_when_unknown_resource_type(self):
        now = datetime.now()
        asset, rels = _build_from_rule(
            organization_id=1,
            resource={"resource_type": "nonexistent_table", "details": {"name": "test"}},
            now=now,
        )
        assert asset is None
        assert rels == []


# ---------------------------------------------------------------------------
# Tests for status resolution (used as fallback in _build_from_rule)
# ---------------------------------------------------------------------------
class TestResolveStatus:
    def test_active_states(self):
        assert _resolve_status({"State": "running"}) == "Active"
        assert _resolve_status({"State": "available"}) == "Active"
        assert _resolve_status({"status": "active"}) == "Active"
        assert _resolve_status({"InstanceState": "in-use"}) == "Active"

    def test_stopped_states(self):
        assert _resolve_status({"State": "stopped"}) == "Stopped"
        assert _resolve_status({"State": "terminated"}) == "Stopped"

    def test_pending_states(self):
        assert _resolve_status({"status": "pending"}) == "Pending"
        assert _resolve_status({"State": "creating"}) == "Pending"

    def test_handles_nested_state_dict(self):
        assert _resolve_status({"State": {"Name": "running"}}) == "Active"

    def test_returns_none_when_no_status(self):
        assert _resolve_status({}) is None


# ---------------------------------------------------------------------------
# Tests for run_query
# ---------------------------------------------------------------------------
class TestRunQuery:
    def test_returns_rows_on_success(self):
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        mock_subprocess.stdout = json.dumps({"rows": [{"name": "test"}]})

        with patch("app.services.steampipe_aws.subprocess.run", return_value=mock_subprocess):
            result = run_query("select * from test;", "/tmp/steampipe", timeout_sec=30)
        assert result == [{"name": "test"}]

    def test_returns_empty_on_error(self):
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 1
        mock_subprocess.stderr = "error"

        with patch("app.services.steampipe_aws.subprocess.run", return_value=mock_subprocess):
            result = run_query("select * from test;", "/tmp/steampipe", timeout_sec=30)
        assert result == []

    def test_returns_empty_on_timeout(self):
        exc = subprocess.TimeoutExpired(cmd="test", timeout=30)
        with patch("app.services.steampipe_aws.subprocess.run", side_effect=exc):
            result = run_query("select * from test;", "/tmp/steampipe", timeout_sec=30)
        assert result == []

    def test_returns_empty_on_json_error(self):
        mock_subprocess = MagicMock()
        mock_subprocess.returncode = 0
        mock_subprocess.stdout = "not json"

        with patch("app.services.steampipe_aws.subprocess.run", return_value=mock_subprocess):
            result = run_query("select * from test;", "/tmp/steampipe", timeout_sec=30)
        assert result == []


# ---------------------------------------------------------------------------
# Integration test for the full Steampipe import flow
# ---------------------------------------------------------------------------
def test_full_steampipe_import_flow():
    """Test that steampipe_aws produces resources with correct canonical_type."""
    from app.services.steampipe_aws import import_aws_resources_via_steampipe

    # Mock STEAMPIPE_TABLE_TO_TYPE to only include the tables we want to test
    mock_mapping = {
        "aws_s3_bucket": "Storage",
        "aws_ec2_instance": "Compute",
    }

    # Mock Path.home() to return a path without .steampipe so symlinks are skipped
    mock_home = Path(tempfile.mkdtemp(prefix="steampipe_home_"))

    with (
        patch("app.services.steampipe_aws.STEAMPIPE_TABLE_TO_TYPE", mock_mapping),
        patch("app.services.steampipe_aws._assume_role") as mock_assume,
        patch("app.services.steampipe_aws.boto3.Session") as mock_session_class,
        patch("app.services.steampipe_aws.subprocess.Popen") as mock_popen,
        patch("pathlib.Path.home", return_value=mock_home),
    ):
        mock_assume.return_value = {
            "AccessKeyId": "ASIA_TEST",
            "SecretAccessKey": "TEST_SECRET",
            "SessionToken": "TEST_TOKEN",
        }

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_sts = MagicMock()
        mock_session.client.return_value = mock_sts
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}

        # _query_table uses subprocess.Popen + proc.communicate(timeout=...),
        # not subprocess.run. Build a fake Popen whose communicate() returns
        # the canned Steampipe JSON output for each table.
        queries_run = []

        def fake_popen(cmd, **kwargs):
            proc = MagicMock()
            query = cmd[2] if len(cmd) > 2 else ""
            queries_run.append(query)

            if "aws_s3_bucket" in query:
                out = json.dumps({
                    "rows": [
                        {
                            "name": "my-bucket",
                            "arn": "arn:aws:s3:::my-bucket",
                            "region": "us-east-1",
                            "account_id": "123456789012",
                        },
                        # Null-arn row must be skipped — no "unknown" asset.
                        {"arn": None},
                    ]
                })
            elif "aws_ec2_instance" in query:
                out = json.dumps({
                    "rows": [{
                        "instance_id": "i-abc",
                        "arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-abc",
                        "instance_type": "t3.medium",
                        "region": "us-east-1",
                    }]
                })
            else:
                out = json.dumps({"rows": []})
            proc.communicate.return_value = (out, "")
            proc.returncode = 0
            return proc

        mock_popen.side_effect = fake_popen

        result = asyncio.run(import_aws_resources_via_steampipe(
            role_arn="arn:aws:iam::123456789012:role/test-role",
            region="us-east-1",
        ))

        assert result["account_id"] == "123456789012"
        # The null-arn s3 row is skipped, so still exactly 2 resources.
        assert result["resources_discovered"] == 2

        resources = result["resources_detail"]
        s3 = [r for r in resources if r["resource_type"] == "aws_s3_bucket"]
        ec2 = [r for r in resources if r["resource_type"] == "aws_ec2_instance"]

        assert len(s3) == 1
        assert s3[0]["resource_id"] != "unknown"
        assert s3[0]["canonical_type"] == "Storage"
        assert s3[0]["resource_id"] == "arn:aws:s3:::my-bucket"

        assert len(ec2) == 1
        assert ec2[0]["canonical_type"] == "Compute"
        assert ec2[0]["resource_id"] == "arn:aws:ec2:us-east-1:123456789012:instance/i-abc"

        # Inventory mode: every query selects only the identifier column.
        assert queries_run
        assert all(q.startswith("select arn from ") for q in queries_run)
