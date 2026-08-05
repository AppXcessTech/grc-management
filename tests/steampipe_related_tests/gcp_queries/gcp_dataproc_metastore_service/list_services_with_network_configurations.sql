select
  name,
  network,
  network_config,
  location
from
  gcp_dataproc_metastore_service
where
  network is not null;