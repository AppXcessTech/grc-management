#!/usr/bin/env python3
"""Generate YAML rule files from static mapping data.

This script has the mapping data INLINE so it doesn't depend on the
app package (which now loads rules from the YAML files itself).
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = PROJECT_ROOT / "rules"

# ── Mapping data: (table_name, canonical_category) ─────────────────
AWS_MAPPINGS = [
    ("aws_accessanalyzer_analyzer", "Monitoring"),
    ("aws_accessanalyzer_finding", "ComplianceFinding"),
    ("aws_acm_certificate", "Certificate"),
    ("aws_cloudtrail_trail", "Logging"),
    ("aws_cloudwatch_alarm", "Monitoring"),
    ("aws_cloudwatch_log_group", "Logging"),
    ("aws_codecommit_repository", "Repository"),
    ("aws_config_configuration_recorder", "ComplianceFinding"),
    ("aws_docdb_cluster", "Database"),
    ("aws_dynamodb_table", "Database"),
    ("aws_ebs_volume", "Storage"),
    ("aws_ec2_application_load_balancer", "LoadBalancer"),
    ("aws_ec2_autoscaling_group", "Compute"),
    ("aws_ec2_classic_load_balancer", "LoadBalancer"),
    ("aws_ec2_instance", "Compute"),
    ("aws_ec2_network_load_balancer", "LoadBalancer"),
    ("aws_ecr_image_scan_finding", "Vulnerability"),
    ("aws_ecr_repository", "ContainerRegistry"),
    ("aws_ecs_cluster", "Container"),
    ("aws_ecs_service", "Container"),
    ("aws_ecs_task", "Container"),
    ("aws_efs_file_system", "Storage"),
    ("aws_eks_cluster", "Container"),
    ("aws_eks_node_group", "Compute"),
    ("aws_guardduty_detector", "Monitoring"),
    ("aws_guardduty_finding", "ThreatFinding"),
    ("aws_iam_account_password_policy", "Policy"),
    ("aws_iam_credential_report", "ComplianceFinding"),
    ("aws_iam_group", "Group"),
    ("aws_iam_policy", "Policy"),
    ("aws_iam_role", "Role"),
    ("aws_iam_user", "Identity"),
    ("aws_identitystore_user", "Identity"),
    ("aws_inspector2_finding", "Vulnerability"),
    ("aws_kms_key", "EncryptionKey"),
    ("aws_lambda_function", "Serverless"),
    ("aws_organizations_account", "Identity"),
    ("aws_rds_db_instance", "Database"),
    ("aws_redshift_cluster", "DataWarehouse"),
    ("aws_s3_bucket", "Storage"),
    ("aws_securityhub_finding", "ComplianceFinding"),
    ("aws_securityhub_hub", "Monitoring"),
    ("aws_sqs_queue", "Application"),
    ("aws_vpc", "Network"),
    ("aws_vpc_flow_log", "Logging"),
    ("aws_vpc_network_acl", "Firewall"),
    ("aws_vpc_route_table", "Network"),
    ("aws_vpc_security_group", "Firewall"),
    ("aws_vpc_subnet", "Network"),
]

GCP_MAPPINGS = [
    # Identity / Service Account
    ("gcp_service_account", "ServiceAccount"),
    ("gcp_service_account_key", "ServiceAccount"),

    # Group
    ("gcp_cloud_identity_group", "Group"),
    ("gcp_cloud_identity_group_membership", "Group"),

    # Role
    ("gcp_iam_role", "Role"),
    ("gcp_iam_policy", "Role"),

    # Compute
    ("gcp_compute_instance", "Compute"),
    ("gcp_compute_instance_group", "Compute"),
    ("gcp_compute_instance_group_manager", "Compute"),
    ("gcp_compute_instance_template", "Compute"),
    ("gcp_compute_autoscaler", "Compute"),
    ("gcp_compute_image", "Compute"),
    ("gcp_compute_machine_image", "Compute"),
    ("gcp_compute_node_group", "Compute"),
    ("gcp_compute_node_template", "Compute"),
    ("gcp_compute_tpu", "Compute"),
    ("gcp_tpu_vm", "Compute"),
    ("gcp_workstations_workstation", "Compute"),
    ("gcp_workstations_workstation_cluster", "Compute"),
    ("gcp_dataproc_cluster", "Compute"),

    # Serverless
    ("gcp_cloudfunctions_function", "Serverless"),
    ("gcp_cloud_run_job", "Serverless"),
    ("gcp_cloud_run_service", "Serverless"),
    ("gcp_app_engine_application", "Serverless"),

    # Container / K8s Cluster
    ("gcp_kubernetes_cluster", "Container"),
    ("gcp_kubernetes_node_pool", "Container"),

    # Container Registry
    ("gcp_artifact_registry_repository", "ContainerRegistry"),

    # Storage
    ("gcp_storage_bucket", "Storage"),
    ("gcp_storage_object", "Storage"),
    ("gcp_compute_disk", "Storage"),

    # Database
    ("gcp_sql_database", "Database"),
    ("gcp_sql_database_instance", "Database"),
    ("gcp_alloydb_cluster", "Database"),
    ("gcp_alloydb_instance", "Database"),
    ("gcp_bigtable_instance", "Database"),
    ("gcp_firestore_database", "Database"),
    ("gcp_dataproc_metastore_service", "Database"),

    # Data Warehouse
    ("gcp_bigquery_dataset", "DataWarehouse"),
    ("gcp_bigquery_table", "DataWarehouse"),

    # Cache
    ("gcp_redis_cluster", "Cache"),
    ("gcp_redis_instance", "Cache"),

    # Backup / Snapshot
    ("gcp_sql_backup", "Backup"),
    ("gcp_compute_snapshot", "Backup"),
    ("gcp_compute_resource_policy", "Backup"),

    # Network
    ("gcp_compute_network", "Network"),
    ("gcp_compute_subnetwork", "Network"),
    ("gcp_compute_address", "Network"),
    ("gcp_compute_global_address", "Network"),
    ("gcp_compute_route", "Network"),
    ("gcp_compute_router", "Network"),
    ("gcp_vpc_access_connector", "Network"),

    # Firewall
    ("gcp_compute_firewall", "Firewall"),
    ("gcp_compute_security_policy", "Firewall"),

    # Load Balancer
    ("gcp_compute_backend_bucket", "LoadBalancer"),
    ("gcp_compute_backend_service", "LoadBalancer"),
    ("gcp_compute_forwarding_rule", "LoadBalancer"),
    ("gcp_compute_global_forwarding_rule", "LoadBalancer"),
    ("gcp_compute_target_https_proxy", "LoadBalancer"),
    ("gcp_compute_target_pool", "LoadBalancer"),
    ("gcp_compute_target_ssl_proxy", "LoadBalancer"),
    ("gcp_compute_url_map", "LoadBalancer"),
    ("gcp_compute_ssl_policy", "LoadBalancer"),

    # DNS
    ("gcp_dns_managed_zone", "DNS"),
    ("gcp_dns_policy", "DNS"),
    ("gcp_dns_record_set", "DNS"),

    # VPN / Gateway
    ("gcp_compute_ha_vpn_gateway", "VPN"),
    ("gcp_compute_vpn_tunnel", "VPN"),
    ("gcp_compute_target_vpn_gateway", "VPN"),

    # Secret
    ("gcp_secret_manager_secret", "Secret"),
    ("gcp_apikeys_key", "Secret"),

    # Encryption Key
    ("gcp_kms_key", "EncryptionKey"),
    ("gcp_kms_key_ring", "EncryptionKey"),
    ("gcp_kms_key_version", "EncryptionKey"),

    # Logging
    ("gcp_logging_bucket", "Logging"),
    ("gcp_logging_exclusion", "Logging"),
    ("gcp_logging_log_entry", "Logging"),
    ("gcp_logging_metric", "Logging"),
    ("gcp_logging_sink", "Logging"),
    ("gcp_audit_policy", "Logging"),
    ("gcp_organization_audit_policy", "Logging"),

    # Monitoring / Alert
    ("gcp_monitoring_alert_policy", "Monitoring"),
    ("gcp_monitoring_group", "Monitoring"),
    ("gcp_monitoring_notification_channel", "Monitoring"),

    # Compliance Finding
    ("gcp_project_organization_policy", "ComplianceFinding"),

    # Organization (extended category)
    ("gcp_organization", "Organization"),
    ("gcp_organization_project", "Organization"),
    ("gcp_project", "Organization"),
    ("gcp_project_service", "Organization"),
    ("gcp_billing_account", "Organization"),
    ("gcp_billing_budget", "Organization"),
]

AZURE_MAPPINGS = [
    ("azure_compute_virtual_machine", "Compute"),
    ("azure_compute_virtual_machine_scale_set", "Compute"),
    ("azure_compute_virtual_machine_scale_set_vm", "Compute"),
    ("azure_kubernetes_cluster", "Container"),
    ("azure_container_group", "Container"),
    ("azure_container_registry", "ContainerRegistry"),
    ("azure_app_service_function_app", "Serverless"),
    ("azure_storage_account", "Storage"),
    ("azure_storage_queue", "Application"),
    ("azure_sql_database", "Database"),
    ("azure_mysql_server", "Database"),
    ("azure_mysql_flexible_server", "Database"),
    ("azure_postgresql_server", "Database"),
    ("azure_postgresql_flexible_server", "Database"),
    ("azure_mariadb_server", "Database"),
    ("azure_mssql_managed_instance", "Database"),
    ("azure_mssql_virtual_machine", "Database"),
    ("azure_cosmosdb_account", "Database"),
    ("azure_cosmosdb_sql_database", "Database"),
    ("azure_cosmosdb_mongo_database", "Database"),
    ("azure_synapse_workspace", "DataWarehouse"),
    ("azure_virtual_network", "Network"),
    ("azure_subnet", "Network"),
    ("azure_network_security_group", "Firewall"),
    ("azure_route_table", "Network"),
    ("azure_lb", "LoadBalancer"),
    ("azure_lb_backend_address_pool", "Network"),
    ("azure_lb_rule", "Network"),
    ("azure_application_gateway", "LoadBalancer"),
    ("azure_log_alert", "Monitoring"),
    ("azure_diagnostic_setting", "Logging"),
    ("azure_monitor_log_profile", "Logging"),
    ("azure_security_center_sub_assessment", "ComplianceFinding"),
    ("azure_role_definition", "Role"),
    ("azure_role_assignment", "Role"),
    ("azure_subscription", "Identity"),
]

# Map canonical_category (string) → directory name (lowercase with underscore)
# This covers all 44 CanonicalType categories the user specified.
CATEGORY_TO_DIR = {
    "Identity": "identity",
    "Group": "group",
    "Role": "role",
    "ServiceAccount": "service_account",
    "Compute": "compute",
    "Serverless": "serverless",
    "Container": "container",
    "ContainerRegistry": "container_registry",
    "Storage": "storage",
    "Database": "database",
    "DataWarehouse": "data_warehouse",
    "Cache": "cache",
    "Backup": "backup",
    "Network": "network",
    "Firewall": "firewall",
    "LoadBalancer": "load_balancer",
    "DNS": "dns",
    "VPN": "vpn",
    "Secret": "secret",
    "Certificate": "certificate",
    "EncryptionKey": "encryption_key",
    "Logging": "logging",
    "Policy": "policy",
    "Monitoring": "monitoring",
    "ThreatFinding": "threat_finding",
    "Vulnerability": "vulnerability",
    "ComplianceFinding": "compliance_finding",
    "Application": "application",
    "Repository": "repository",
    "Pipeline": "pipeline",
    "Deployment": "deployment",
    "Artifact": "artifact",
    "Webhook": "webhook",
    "Organization": "organization",
    "Device": "device",
    "MobileDevice": "mobile_device",
    "EndpointProtection": "endpoint_protection",
    "Employee": "employee",
    "BackgroundCheck": "background_check",
    "SecurityTraining": "security_training",
    "PolicyAcknowledgement": "policy_acknowledgement",
    "Vendor": "vendor",
    "VendorAssessment": "vendor_assessment",
    "NDA": "nda",
    "Ticket": "ticket",
}


# ── Per-resource canonical_id_template overrides ────────────────────
# AWS rules uniformly use `$.arn` as the canonical identifier (the Resource ID
# shown for every AWS asset), except for a handful of tables that have NO arn
# column in Steampipe — those use their native identifier column so the ID
# never resolves to "unknown".
AWS_ID_TEMPLATES: dict[str, str] = {
    "aws_vpc_flow_log": "$.flow_log_id",
    "aws_ecr_image_scan_finding": "$.name",
    "aws_iam_account_password_policy": "$.account_id",
    "aws_iam_credential_report": "$.user_arn",
    "aws_identitystore_user": "$.name",
}

GCP_ID_TEMPLATES: dict[str, str] = {
    "gcp_iam_role": "$.arn or $.name or $.id or $.self_link",
    "gcp_iam_policy": "$.arn or $.name or $.id or $.self_link",
}

AZURE_ID_TEMPLATES: dict[str, str] = {}


def _yaml_str(value: str) -> str:
    """Quote a string value for YAML if needed."""
    if any(c in value for c in ":{}[],&*?|>!%@`"):
        return f"'{value}'"
    return value


def _get_id_template(table_name: str, provider: str) -> str:
    """Get the canonical_id_template for a given table and provider.

    Uses per-resource mappings first, then falls back to a generic template
    with resource-specific fields for the provider.
    """
    # Check per-resource maps first, then generic fallbacks.
    # AWS rules use `$.arn` as the canonical identifier, except for tables
    # without an arn column (AWS_ID_TEMPLATES). GCP/Azure keep a short
    # fallback chain ending in $.title as a safety net.
    if provider == "AWS":
        return AWS_ID_TEMPLATES.get(table_name, "$.arn")
    if provider == "Azure":
        if table_name in AZURE_ID_TEMPLATES:
            return AZURE_ID_TEMPLATES[table_name] + " or $.title"
        return "$.id or $.name or $.title"
    if provider == "GCP":
        if table_name in GCP_ID_TEMPLATES:
            return GCP_ID_TEMPLATES[table_name] + " or $.title"
        return "$.id or $.name or $.self_link or $.title"
    return "$.id or $.name or $.title"


def _generate_yaml(table_name: str, category: str, provider: str) -> str:
    """Generate YAML content for a single rule file."""

    id_expr = _get_id_template(table_name, provider)

    source_system = {
        "AWS": "aws",
        "Azure": "azure",
        "GCP": "gcp",
    }.get(provider, provider.lower())

    # AWS rules show the ARN as the display ID (the assets table's "ID"
    # column), so display_name maps to $.arn — except for tables without an
    # arn column, which use their native identifier. Other providers keep
    # the name-based fallback chain.
    display_name_expr = AWS_ID_TEMPLATES.get(table_name, "$.arn") if provider == "AWS" else "$.name or $.Name or $.id or $.self_link or $.title"

    lines = [
        f"source_table: {table_name}",
        f"canonical_category: {category}",
        f"provider: {provider}",
        f"canonical_id_template: {_yaml_str(id_expr)}",
        "",
        "mappings:",
        f"  display_name: {_yaml_str(display_name_expr)}",
        f"  region: {_yaml_str('$.region')}",
        f"  account_id: {_yaml_str('$.account_id')}",
    ]

    if provider == "Azure":
        lines.append(f"  subscription_id: {_yaml_str('$.subscription_id')}")
    elif provider == "GCP":
        lines.append(f"  project: {_yaml_str('$.project')}")

    lines.extend([
        "",
        "required_canonical_fields:",
        "  - display_name",
        "",
        "defaults:",
        f"  source_system: {source_system}",
        "",
        "version: 1",
        "last_modified: '2026-07-30'",
        "",
    ])
    return "\n".join(lines)


def _provider_for_table(table_name: str) -> str:
    """Derive the provider name from a Steampipe table name prefix."""
    if table_name.startswith("gcp_"):
        return "GCP"
    if table_name.startswith("aws_"):
        return "AWS"
    if table_name.startswith("azure_"):
        return "Azure"
    if table_name.startswith("okta_"):
        return "Okta"
    if table_name.startswith("github_"):
        return "GitHub"
    if table_name.startswith("microsoft365_"):
        return "Microsoft365"
    return "Other"


def main():
    created = 0
    for table_name, category in AWS_MAPPINGS + GCP_MAPPINGS + AZURE_MAPPINGS:
        provider = _provider_for_table(table_name)
        dir_name = CATEGORY_TO_DIR.get(category, "other")
        target_dir = RULES_DIR / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)

        yaml_content = _generate_yaml(table_name, category, provider)
        yaml_path = target_dir / f"{table_name}.yaml"
        yaml_path.write_text(yaml_content)
        created += 1
        print(f"  ✓ {yaml_path.relative_to(PROJECT_ROOT)}")

    print(f"\n✅ Generated {created} rule files under {RULES_DIR}")


if __name__ == "__main__":
    main()
