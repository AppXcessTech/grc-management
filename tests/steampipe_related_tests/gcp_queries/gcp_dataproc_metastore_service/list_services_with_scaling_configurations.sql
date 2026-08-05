select
  name,
  scaling_config,
  project,
  location
from
  gcp_dataproc_metastore_service
where
  scaling_config is not null;