import os
import re
import time
import requests

BASE_URL = "https://raw.githubusercontent.com/turbot/steampipe-plugin-azure/main/docs/tables"

TABLES = [
    "azure_log_alert",                                    # Azure Activity Log Alert
    "azure_kubernetes_cluster",                            # Azure AKS Cluster
    "azure_compute_virtual_machine_scale_set_vm",          # Azure AKS Node (closest match -- AKS nodes are VMSS VMs)
    "azure_container_group",                               # Azure Application Container (ACI)
    "azure_application_gateway",                           # Azure Application Gateway
    "azure_container_registry",                            # Azure Container Repository
    "azure_security_center_sub_assessment",                # Azure Container Vulnerability (closest match)
    "azure_cosmosdb_account",                               # Azure CosmosDB
    "azure_cosmosdb_sql_database",                          # Azure CosmosDB (SQL API databases -- not in your list, but likely needed alongside account)
    "azure_cosmosdb_mongo_database",                        # Azure CosmosDB (Mongo API databases -- not in your list, but likely needed alongside account)
    # "azure_cosmosdb_postgresql_...",                      # Azure CosmosDB for PostgreSQL -- NOT AVAILABLE in steampipe-plugin-azure, no table found
    "azure_sql_database",                                   # Azure Database (SQL)
    "azure_mysql_server",                                   # Azure Database (MySQL)
    "azure_mysql_flexible_server",                          # Azure Database (MySQL Flexible)
    "azure_postgresql_server",                              # Azure Database (PostgreSQL)
    "azure_postgresql_flexible_server",                     # Azure Database (PostgreSQL Flexible)
    "azure_mariadb_server",                                 # Azure Database (MariaDB)
    "azure_diagnostic_setting",                             # Azure Diagnostic Setting
    "azure_app_service_function_app",                       # Azure Function
    "azure_lb",                                             # Azure Load Balancer
    "azure_lb_backend_address_pool",                        # Azure Load Balancer (backend pools -- not in your list, but likely needed alongside lb)
    "azure_lb_rule",                                        # Azure Load Balancer (rules -- not in your list, but likely needed alongside lb)
    "azure_monitor_log_profile",                            # Azure Log Alert (related profile-level data)
    # "azure_monitor_metric_alert",                         # Azure Metric Alert Rule -- NOT FOUND in current steampipe-plugin-azure table docs
    "azure_storage_queue",                                  # Azure Queue
    "azure_role_definition",                                # Azure Role
    "azure_role_assignment",                                # Azure Role Assignment
    "azure_route_table",                                    # Azure Route Table
    "azure_compute_virtual_machine_scale_set_vm",           # Azure Scale Set Virtual Machine
    "azure_network_security_group",                         # Azure Security Group
    "azure_security_center_sub_assessment",                 # Azure Server Vulnerability (closest match)
    "azure_sql_database",                                   # Azure SQL Database
    "azure_mssql_managed_instance",                         # Azure SQL Managed Instance
    "azure_mssql_virtual_machine",                          # Azure SQL Server on Virtual Machine
    "azure_storage_account",                                # Azure Storage Account
    "azure_subnet",                                         # Azure Subnet
    "azure_subscription",                                   # Azure Subscription
    "azure_synapse_workspace",                              # Azure Synapse Warehouse (closest match)
    "azure_compute_virtual_machine",                        # Azure Virtual Machine
    "azure_compute_virtual_machine_scale_set",              # Azure Virtual Machine Scale Set
    "azure_virtual_network",                                # Azure Virtual Network
]

OUTPUT_ROOT = "queries_azure"

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
