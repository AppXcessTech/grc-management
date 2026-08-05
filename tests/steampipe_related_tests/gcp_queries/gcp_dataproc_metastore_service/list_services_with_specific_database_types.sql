select
  name,
  database_type,
  location,
  project
from
  gcp_dataproc_metastore_service
where
  database_type = 'MYSQL';