import os
import re
import time
import requests

BASE_URL = "https://raw.githubusercontent.com/turbot/steampipe-plugin-gcp/main/docs/tables"

TABLES = [
    # Identity / Service Account
    "gcp_service_account",                       # Service Account / App Identity
    "gcp_service_account_key",                   # Service Account / App Identity

    # Group
    "gcp_cloud_identity_group",                  # Group
    "gcp_cloud_identity_group_membership",       # Group

    # Role
    "gcp_iam_role",                              # Role
    "gcp_iam_policy",                            # Role

    # Compute
    "gcp_compute_instance",                      # Compute
    "gcp_compute_instance_group",                # Compute
    "gcp_compute_instance_group_manager",        # Compute
    "gcp_compute_instance_template",             # Compute
    "gcp_compute_autoscaler",                    # Compute
    "gcp_compute_image",                         # Compute
    "gcp_compute_machine_image",                 # Compute
    "gcp_compute_node_group",                    # Compute
    "gcp_compute_node_template",                 # Compute
    "gcp_compute_tpu",                           # Compute (deprecated, superseded by gcp_tpu_vm)
    "gcp_tpu_vm",                                # Compute
    "gcp_workstations_workstation",              # Compute
    "gcp_workstations_workstation_cluster",      # Compute
    "gcp_dataproc_cluster",                      # Compute

    # Serverless
    "gcp_cloudfunctions_function",               # Serverless
    "gcp_cloud_run_job",                         # Serverless
    "gcp_cloud_run_service",                     # Serverless
    "gcp_app_engine_application",                # Serverless
 
    # Container / K8s Cluster
    "gcp_kubernetes_cluster",                    # Container / K8s Cluster
    "gcp_kubernetes_node_pool",                  # Container / K8s Cluster
 
    # Container Registry
    "gcp_artifact_registry_repository",          # Container Registry
 
    # Storage
    "gcp_storage_bucket",                        # Storage
    "gcp_storage_object",                        # Storage
    "gcp_compute_disk",                          # Storage
 
    # Database
    "gcp_sql_database",                          # Database
    "gcp_sql_database_instance",                 # Database
    "gcp_alloydb_cluster",                       # Database
    "gcp_alloydb_instance",                      # Database
    "gcp_bigtable_instance",                     # Database
    "gcp_firestore_database",                    # Database
    "gcp_dataproc_metastore_service",            # Database
 
    # Data Warehouse
    "gcp_bigquery_dataset",                      # Data Warehouse
    "gcp_bigquery_table",                        # Data Warehouse
 
    # Cache
    "gcp_redis_cluster",                         # Cache
    "gcp_redis_instance",                        # Cache
 
    # Backup / Snapshot
    "gcp_sql_backup",                            # Backup / Snapshot
    "gcp_compute_snapshot",                      # Backup / Snapshot
    "gcp_compute_resource_policy",               # Backup / Snapshot (snapshot scheduling policy)
 
    # Network
    "gcp_compute_network",                       # Network
    "gcp_compute_subnetwork",                    # Network
    "gcp_compute_address",                       # Network
    "gcp_compute_global_address",                # Network
    "gcp_compute_route",                         # Network
    "gcp_compute_router",                        # Network
    "gcp_vpc_access_connector",                  # Network
 
    # Firewall
    "gcp_compute_firewall",                      # Firewall
    "gcp_compute_security_policy",               # Firewall
 
    # Load Balancer
    "gcp_compute_backend_bucket",                # Load Balancer
    "gcp_compute_backend_service",               # Load Balancer
    "gcp_compute_forwarding_rule",               # Load Balancer
    "gcp_compute_global_forwarding_rule",        # Load Balancer
    "gcp_compute_target_https_proxy",            # Load Balancer
    "gcp_compute_target_pool",                   # Load Balancer
    "gcp_compute_target_ssl_proxy",              # Load Balancer
    "gcp_compute_url_map",                       # Load Balancer
    "gcp_compute_ssl_policy",                    # Load Balancer
 
    # DNS
    "gcp_dns_managed_zone",                      # DNS
    "gcp_dns_policy",                            # DNS
    "gcp_dns_record_set",                        # DNS
 
    # VPN / Gateway
    "gcp_compute_ha_vpn_gateway",                # VPN / Gateway
    "gcp_compute_vpn_tunnel",                    # VPN / Gateway
    "gcp_compute_target_vpn_gateway",            # VPN / Gateway
 
    # Secret
    "gcp_secret_manager_secret",                 # Secret
    "gcp_apikeys_key",                           # Secret
 
    # Encryption Key
    "gcp_kms_key",                               # Encryption Key
    "gcp_kms_key_ring",                          # Encryption Key
    "gcp_kms_key_version",                       # Encryption Key
 
    # Logging
    "gcp_logging_bucket",                        # Logging
    "gcp_logging_exclusion",                     # Logging
    "gcp_logging_log_entry",                     # Logging
    "gcp_logging_metric",                        # Logging
    "gcp_logging_sink",                          # Logging
    "gcp_audit_policy",                          # Logging
    "gcp_organization_audit_policy",             # Logging
 
    # Monitoring / Alert
    "gcp_monitoring_alert_policy",               # Monitoring / Alert
    "gcp_monitoring_group",                      # Monitoring / Alert
    "gcp_monitoring_notification_channel",       # Monitoring / Alert
 
    # Compliance Finding
    "gcp_project_organization_policy",           # Compliance Finding
 
    # Organization (extended category, alongside azure_subscription / aws_organizations_account)
    "gcp_organization",                          # Organization
    "gcp_organization_project",                  # Organization
    "gcp_project",                               # Organization
    "gcp_project_service",                       # Organization
    "gcp_billing_account",                       # Organization
    "gcp_billing_budget",                        # Organization
]



OUTPUT_ROOT = "gcp_queries"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ### Heading followed by the next sql+postgres block
PATTERN = re.compile(
    r"###\s+(.*?)\n.*?```sql\+postgres\s*(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

for table in TABLES:
    url = f"{BASE_URL}/{table}.md"

    print(f"Fetching {table}...")

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        markdown = response.text

        matches = PATTERN.findall(markdown)

        if not matches:
            print("❌ No queries found.")
            continue

        table_dir = os.path.join(OUTPUT_ROOT, table)
        os.makedirs(table_dir, exist_ok=True)

        for heading, query in matches:

            # Convert heading into a safe filename
            filename = heading.lower().strip()
            filename = re.sub(r"[^\w\s-]", "", filename)
            filename = re.sub(r"\s+", "_", filename)

            output_file = os.path.join(table_dir, f"{filename}.sql")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(query.strip())

        print(f"✅ Saved {len(matches)} queries.")

        time.sleep(0.5)

    except Exception as e:
        print(f"❌ {table}: {e}")
