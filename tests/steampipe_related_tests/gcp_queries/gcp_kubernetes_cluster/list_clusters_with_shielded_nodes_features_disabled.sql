select
  name,
  location_type,
  shielded_nodes_enabled
from
  gcp_kubernetes_cluster
where
  not shielded_nodes_enabled;