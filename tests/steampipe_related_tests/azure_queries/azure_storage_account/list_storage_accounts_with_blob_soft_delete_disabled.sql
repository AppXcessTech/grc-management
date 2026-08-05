select
  name,
  blob_soft_delete_enabled,
  blob_soft_delete_retention_days
from
  azure_storage_account
where
  not blob_soft_delete_enabled;