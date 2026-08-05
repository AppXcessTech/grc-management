select
  name,
  state,
  state_message,
  location
from
  gcp_dataproc_metastore_service
where
  state = 'ACTIVE';