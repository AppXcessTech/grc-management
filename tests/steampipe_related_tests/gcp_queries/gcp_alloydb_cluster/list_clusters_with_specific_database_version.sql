select
  name,
  database_version,
  state,
  location
from
  gcp_alloydb_cluster
where
  database_version = 'POSTGRES_14';