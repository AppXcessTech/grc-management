select
  name,
  location_type
from
  gcp_kubernetes_node_pool
where
  location_type = 'ZONAL';