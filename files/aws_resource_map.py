"""
AWS Resource -> Canonical Type Mapper
=======================================
Maps every AWS resource type Vanta imports to a canonical_type (from the
44-category taxonomy) and defines the expected `details` fields for each.

Usage:
    from aws_resource_map import RESOURCE_MAP

    entry = RESOURCE_MAP["aws_ec2_instance"]
    asset = Asset(
        provider="aws",
        canonical_type=entry["canonical_type"],
        details={field: raw_data.get(field) for field in entry["detail_fields"]},
        ...
    )
"""

RESOURCE_MAP = {

    "aws_access_analyzer": {
        "name": "AWS Access Analyzer",
        "canonical_type": "compliance_finding",
        "detail_fields": ["finding_id", "resource_type", "is_public", "condition", "status"],
    },
    "aws_autoscaling_group": {
        "name": "AWS Autoscaling Group",
        "canonical_type": "compute",
        "detail_fields": ["min_size", "max_size", "desired_capacity", "launch_template", "instance_ids"],
    },
    "aws_certificate": {
        "name": "AWS Certificate",
        "canonical_type": "certificate",
        "detail_fields": ["expiry_date", "issuer", "key_length", "domain_name", "status"],
    },
    "aws_cloudtrail": {
        "name": "AWS CloudTrail",
        "canonical_type": "logging",
        "detail_fields": ["is_multi_region", "log_file_validation_enabled", "is_logging", "kms_key_id"],
    },
    "aws_cloudwatch_log_group": {
        "name": "AWS CloudWatch Log Group",
        "canonical_type": "logging",
        "detail_fields": ["retention_days", "stored_bytes", "kms_key_id"],
    },
    "aws_cloudwatch_metric_alarm": {
        "name": "AWS CloudWatch Metric Alarm",
        "canonical_type": "monitoring_alert",
        "detail_fields": ["metric_name", "threshold", "comparison_operator", "alarm_actions", "state"],
    },
    "aws_codecommit_repo": {
        "name": "AWS CodeCommit Repo",
        "canonical_type": "repository",
        "detail_fields": ["default_branch", "branch_protection", "requires_review", "secret_scanning"],
    },
    "aws_config_recorder": {
        "name": "AWS Config Recorder",
        "canonical_type": "logging",
        "detail_fields": ["recording_enabled", "all_supported", "delivery_channel", "status"],
    },
    "aws_credential_report": {
        "name": "AWS Credential Report",
        "canonical_type": "identity",
        "detail_fields": ["mfa_active", "password_last_used", "access_key_1_last_rotated",
                           "access_key_2_last_rotated", "password_last_changed"],
    },
    "aws_documentdb_cluster": {
        "name": "AWS DocumentDB Cluster",
        "canonical_type": "database",
        "detail_fields": ["encrypted_at_rest", "backup_enabled", "public_access", "engine_version"],
    },
    "aws_dynamodb_table": {
        "name": "AWS DynamoDB Table",
        "canonical_type": "database",
        "detail_fields": ["encrypted_at_rest", "point_in_time_recovery", "kms_key_id", "table_status"],
    },
    "aws_ebs_volume": {
        "name": "AWS EBS Volume",
        "canonical_type": "storage",
        "detail_fields": ["encrypted", "kms_key_id", "size_gb", "attached_instance_id", "volume_type"],
    },
    "aws_ec2_instance": {
        "name": "AWS EC2 Instance",
        "canonical_type": "compute",
        "detail_fields": ["public_ip", "private_ip", "os_version", "encrypted_disk", "instance_type", "ami_id"],
    },
    "aws_ecr_container_repository": {
        "name": "AWS ECR Container Repository",
        "canonical_type": "container_registry",
        "detail_fields": ["scan_on_push", "public", "image_tag_mutability", "encryption_type"],
    },
    "aws_ecr_container_vulnerability": {
        "name": "AWS ECR Container Vulnerability",
        "canonical_type": "vulnerability",
        "detail_fields": ["cve_id", "severity", "package_name", "fixed_in_version", "repository"],
    },
    "aws_ecs_cluster": {
        "name": "AWS ECS Cluster",
        "canonical_type": "container_k8s_cluster",
        "detail_fields": ["active_services_count", "running_tasks_count", "capacity_providers"],
    },
    "aws_ecs_service": {
        "name": "AWS ECS Service",
        "canonical_type": "deployment",
        "detail_fields": ["desired_count", "launch_type", "task_definition", "deployment_controller"],
    },
    "aws_ecs_standalone_task": {
        "name": "AWS ECS Standalone Task",
        "canonical_type": "container_k8s_cluster",
        "detail_fields": ["task_definition_arn", "last_status", "launch_type", "container_instance_arn"],
    },
    "aws_efs_file_system": {
        "name": "AWS EFS File System",
        "canonical_type": "storage",
        "detail_fields": ["encrypted", "kms_key_id", "lifecycle_policy", "performance_mode"],
    },
    "aws_eks_cluster": {
        "name": "AWS EKS Cluster",
        "canonical_type": "container_k8s_cluster",
        "detail_fields": ["rbac_enabled", "network_policy", "endpoint_public_access", "k8s_version",
                           "logging_types_enabled"],
    },
    "aws_eks_node": {
        "name": "AWS EKS Node",
        "canonical_type": "compute",
        "detail_fields": ["instance_type", "ami_type", "os_version", "capacity_type"],
    },
    "aws_flow_log": {
        "name": "AWS Flow Log",
        "canonical_type": "logging",
        "detail_fields": ["resource_id", "traffic_type", "log_destination_type", "status"],
    },
    "aws_group": {
        "name": "AWS Group",
        "canonical_type": "group",
        "detail_fields": ["member_count", "attached_policies", "type"],
    },
    "aws_guardduty_detector": {
        "name": "AWS Guard Duty Detector",
        "canonical_type": "threat_finding",
        "detail_fields": ["status", "finding_publishing_frequency", "data_sources_enabled"],
    },
    "aws_iam_identity_center_user": {
        "name": "AWS IAM Identity Center User",
        "canonical_type": "identity",
        "detail_fields": ["mfa_enabled", "status", "last_login", "assigned_permission_sets"],
    },
    "aws_iam_policy": {
        "name": "AWS IAM Policy",
        "canonical_type": "policy",
        "detail_fields": ["permissions", "attachment_count", "is_aws_managed", "policy_document"],
    },
    "aws_iam_user": {
        "name": "AWS IAM User",
        "canonical_type": "identity",
        "detail_fields": ["mfa_enabled", "status", "last_login", "privileged", "attached_policies"],
    },
    "aws_inspector_vulnerability": {
        "name": "AWS Inspector Vulnerability",
        "canonical_type": "vulnerability",
        "detail_fields": ["cve_id", "severity", "remediation_deadline", "affected_resource"],
    },
    "aws_kms_key": {
        "name": "AWS KMS Key",
        "canonical_type": "encryption_key",
        "detail_fields": ["rotation_enabled", "algorithm", "key_policy", "key_state"],
    },
    "aws_lambda_function": {
        "name": "AWS Lambda Function",
        "canonical_type": "serverless",
        "detail_fields": ["runtime", "public_url", "env_vars_encrypted", "execution_role", "last_modified"],
    },
    "aws_load_balancer": {
        "name": "AWS Load Balancer",
        "canonical_type": "load_balancer",
        "detail_fields": ["ssl_policy", "public", "listener_ports", "type"],
    },
    "aws_network_acl": {
        "name": "AWS Network ACL",
        "canonical_type": "firewall_security_group",
        "detail_fields": ["inbound_rules", "outbound_rules", "is_default", "associated_subnets"],
    },
    "aws_organization_account": {
        "name": "AWS Organization Account",
        "canonical_type": "custom",  # no clean fit in the 44-category list -- org-structure metadata,
        "detail_fields": ["account_email", "joined_method", "status", "org_unit_id"],
    },
    "aws_password_policy": {
        "name": "AWS Password Policy",
        "canonical_type": "policy",
        "detail_fields": ["min_length", "require_symbols", "require_numbers", "max_age_days", "reuse_prevention"],
    },
    "aws_rds_instance": {
        "name": "AWS RDS Instance",
        "canonical_type": "database",
        "detail_fields": ["encrypted_at_rest", "backup_enabled", "public_access", "multi_az", "engine"],
    },
    "aws_redshift_cluster": {
        "name": "AWS Redshift Cluster",
        "canonical_type": "data_warehouse",
        "detail_fields": ["encryption", "access_logging", "publicly_accessible", "node_type"],
    },
    "aws_role": {
        "name": "AWS Role",
        "canonical_type": "role",
        "detail_fields": ["permissions", "scope", "assumable_by", "trust_policy"],
    },
    "aws_route_table": {
        "name": "AWS Route Table",
        "canonical_type": "network",
        "detail_fields": ["routes", "associated_subnets", "is_main"],
    },
    "aws_s3_bucket": {
        "name": "AWS S3 Bucket",
        "canonical_type": "storage",
        "detail_fields": ["encrypted", "public", "versioning", "lifecycle_policy", "logging_enabled"],
    },
    "aws_security_group": {
        "name": "AWS Security Group",
        "canonical_type": "firewall_security_group",
        "detail_fields": ["open_ports", "source_ranges", "vpc_id", "inbound_rules", "outbound_rules"],
    },
    "aws_security_hub": {
        "name": "AWS Security Hub",
        "canonical_type": "compliance_finding",
        "detail_fields": ["control_id", "status", "severity", "standard", "workflow_state"],
    },
    "aws_sqs_queue": {
        "name": "AWS SQS Queue",
        "canonical_type": "custom",  # no clean fit -- messaging queue, not infra/identity/data
        "detail_fields": ["encrypted", "kms_key_id", "policy", "visibility_timeout"],
    },
    "aws_subnet": {
        "name": "AWS Subnet",
        "canonical_type": "network",
        "detail_fields": ["cidr", "flow_logs_enabled", "default_deny", "availability_zone", "vpc_id"],
    },
    "aws_vpc": {
        "name": "AWS VPC",
        "canonical_type": "network",
        "detail_fields": ["cidr", "flow_logs_enabled", "default_deny", "is_default"],
    },
}
