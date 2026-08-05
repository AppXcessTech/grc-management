select
  name,
  labels,
  annotations,
  replication,
  ttl
from
  gcp_secret_manager_secret
where
  name = 'my-secret';