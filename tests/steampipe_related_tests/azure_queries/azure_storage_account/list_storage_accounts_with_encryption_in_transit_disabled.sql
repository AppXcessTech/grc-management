select
  name,
  enable_https_traffic_only
from
  azure_storage_account
where
  not enable_https_traffic_only;