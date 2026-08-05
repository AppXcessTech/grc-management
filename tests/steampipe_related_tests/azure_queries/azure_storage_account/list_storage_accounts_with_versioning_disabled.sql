select
  name,
  blob_versioning_enabled
from
  azure_storage_account
where
  not blob_versioning_enabled;