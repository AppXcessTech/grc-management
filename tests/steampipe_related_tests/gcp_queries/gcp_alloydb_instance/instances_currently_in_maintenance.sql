select
  name,
  state
from
  gcp_alloydb_instance
where
  state = 'MAINTENANCE';