select
  name,
  region,
  enable_automatic_failover,
  resource_group
from
  azure_cosmosdb_account
where
  not enable_automatic_failover;