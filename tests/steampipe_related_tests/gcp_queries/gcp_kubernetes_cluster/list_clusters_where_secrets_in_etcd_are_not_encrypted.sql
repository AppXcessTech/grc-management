select
  name,
  database_encryption_state
from
  gcp_kubernetes_cluster
where
  database_encryption_state <> 'ENCRYPTED';