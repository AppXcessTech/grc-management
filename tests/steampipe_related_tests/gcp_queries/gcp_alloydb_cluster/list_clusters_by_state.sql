select
  name,
  state
from
  gcp_alloydb_cluster
where
  state = 'MAINTENANCE';