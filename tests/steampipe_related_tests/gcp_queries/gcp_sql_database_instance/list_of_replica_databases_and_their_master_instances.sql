select
  name,
  master_instance_name,
  replication_type,
  gce_zone as replica_database_zone
from
  gcp_sql_database_instance
where
  database_replication_enabled;