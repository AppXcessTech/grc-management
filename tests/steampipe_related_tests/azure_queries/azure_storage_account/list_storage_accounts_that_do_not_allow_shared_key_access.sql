select
  name,
  allow_shared_key_access
from
  azure_storage_account
where
  not allow_shared_key_access;