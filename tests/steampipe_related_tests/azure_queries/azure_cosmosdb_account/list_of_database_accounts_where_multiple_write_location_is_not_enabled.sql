select
  name,
  region,
  enable_multiple_write_locations
from
  azure_cosmosdb_account
where
  not enable_multiple_write_locations;