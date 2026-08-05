select
  id,
  name,
  bucket,
  size,
  storage_class,
  time_created
from
  gcp_storage_object
where
  bucket = 'steampipe-test';