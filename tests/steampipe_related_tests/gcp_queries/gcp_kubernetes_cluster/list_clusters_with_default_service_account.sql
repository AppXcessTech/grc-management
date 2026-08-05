select
  name,
  location_type,
  node_config ->> 'ServiceAccount' service_account
from
  gcp_kubernetes_cluster
where
  node_config ->> 'ServiceAccount' = 'default';