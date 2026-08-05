select
  name,
  location,
  versioning_enabled
from
  gcp_storage_bucket
where
  not versioning_enabled;