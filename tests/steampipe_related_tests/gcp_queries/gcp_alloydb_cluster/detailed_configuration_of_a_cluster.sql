select
  name,
  encryption_config,
  network_config
from
  gcp_alloydb_cluster
where
  display_name = 'your-cluster-name';