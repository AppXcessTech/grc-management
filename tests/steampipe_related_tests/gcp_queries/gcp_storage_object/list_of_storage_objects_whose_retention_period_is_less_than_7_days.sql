select
  bucket,
  name,
  extract(epoch from (retention_expiration_time - current_timestamp)) as retention_period_secs
from
  gcp_storage_object
where
  extract(epoch from (retention_expiration_time - current_timestamp)) < 604800
  and bucket = 'steampipe-test';