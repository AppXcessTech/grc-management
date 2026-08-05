select
  name,
  location_type
from
  gcp_kubernetes_cluster
where
  location_type = 'ZONAL';