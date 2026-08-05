select
  id,
  name,
  bucket,
  kms_key_name
from
  gcp_storage_object
where
  bucket = 'steampipe-test'
  and kms_key_name != '';