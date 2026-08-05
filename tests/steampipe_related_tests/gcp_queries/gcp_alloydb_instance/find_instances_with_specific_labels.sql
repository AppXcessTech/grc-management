select
  name,
  labels
from
  gcp_alloydb_instance
where
  labels -> 'environment' = 'production';