"""
Tests for GitLab canonical mapping rules.

Verifies that every GitLab Steampipe table defined in the mapping has a
YAML rule file, maps to a valid CanonicalType value, and that the
provider-specific type map exposes them (mirrors TestCanonicalMap in
test_steampipe_aws.py).
"""
import pytest

from app.mappers.canonical_map import (
    GITLAB_STEAMPIPE_TABLE_TO_TYPE,
    get_rule,
    get_type,
)
from app.models.enums import CanonicalType, Provider


EXPECTED_GITLAB_TABLES = [
    # Application
    "gitlab_application",
    # Policy (authentication settings share the Policy category)
    "gitlab_setting",
    # Configuration (CI/CD variables)
    "gitlab_group_variable",
    "gitlab_project_variable",
    "gitlab_instance_variable",
    # Container Registry
    "gitlab_project_container_registry",
    # Deployment
    "gitlab_project_deployment",
    # Group
    "gitlab_group",
    "gitlab_group_subgroup",
    "gitlab_group_project",
    "gitlab_group_member",
    "gitlab_project_member",
    "gitlab_group_access_request",
    "gitlab_project_access_request",
    # Identity
    "gitlab_user",
    # Pipeline
    "gitlab_project_pipeline",
    "gitlab_project_pipeline_detail",
    "gitlab_project_job",
    # Repository
    "gitlab_project",
    "gitlab_my_project",
    "gitlab_project_protected_branch",
    "gitlab_group_push_rule",
    # Webhook
    "gitlab_group_hook",
]


class TestGitlabCanonicalMap:
    def test_all_tables_have_mapping(self):
        """Every known GitLab Steampipe table has a mapping in the YAML rules."""
        for table in EXPECTED_GITLAB_TABLES:
            assert table in GITLAB_STEAMPIPE_TABLE_TO_TYPE, f"Missing mapping for {table}"
            assert isinstance(GITLAB_STEAMPIPE_TABLE_TO_TYPE[table], str), f"{table} not mapped to a string"

    def test_each_category_is_valid_canonical_type(self):
        """All mapped values are valid CanonicalType values."""
        valid = {ct.value for ct in CanonicalType}
        for table, ctype in GITLAB_STEAMPIPE_TABLE_TO_TYPE.items():
            assert ctype in valid, f"{table} -> {ctype} is not a valid CanonicalType"

    def test_get_type_returns_correct_value(self):
        assert get_type("gitlab_project") == "Repository"
        assert get_type("gitlab_group") == "Group"
        assert get_type("gitlab_user") == "Identity"
        assert get_type("gitlab_setting") == "Policy"
        assert get_type("gitlab_group_hook") == "Webhook"

    def test_get_rule_returns_rule_with_provider(self):
        rule = get_rule("gitlab_project")
        assert rule.provider == "GitLab"
        assert rule.canonical_category == "Repository"
        assert rule.source_table == "gitlab_project"

    def test_provider_enum_has_gitlab(self):
        assert Provider.gitlab.value == "GitLab"

    def test_all_rules_have_display_name_mapping(self):
        """Every GitLab rule must define a display_name mapping."""
        for table in EXPECTED_GITLAB_TABLES:
            rule = get_rule(table)
            assert "display_name" in rule.mappings, f"{table} missing display_name mapping"
