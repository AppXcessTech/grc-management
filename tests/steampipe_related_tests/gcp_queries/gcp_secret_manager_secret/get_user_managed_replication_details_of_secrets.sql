select
  name,
  create_time,
  replication -> 'userManaged' -> 'replicas' as user_managed_replicas
from
  gcp_secret_manager_secret;