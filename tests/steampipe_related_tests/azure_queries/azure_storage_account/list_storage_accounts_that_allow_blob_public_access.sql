select
  name,
  allow_blob_public_access
from
  azure_storage_account
where
  allow_blob_public_access;