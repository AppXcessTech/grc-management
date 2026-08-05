select
  name,
  encryption_config
from
  gcp_alloydb_cluster
where
  encryption_config is not null;