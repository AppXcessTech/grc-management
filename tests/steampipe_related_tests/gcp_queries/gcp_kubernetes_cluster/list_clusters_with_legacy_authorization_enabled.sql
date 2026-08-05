select
  name,
  location_type,
  legacy_abac_enabled
from
  gcp_kubernetes_cluster
where
  legacy_abac_enabled;