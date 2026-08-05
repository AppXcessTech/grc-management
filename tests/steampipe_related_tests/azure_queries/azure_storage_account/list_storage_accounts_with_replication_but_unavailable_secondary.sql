select
  name,
  status_of_primary,
  status_of_secondary,
  sku_name
from
  azure_storage_account
where
  status_of_primary = 'available'
  and status_of_secondary != 'available'
  and sku_name in ('Standard_GRS', 'Standard_RAGRS');