select
  name,
  region,
  virtual_network_rules
from
  azure_cosmosdb_account
where
  virtual_network_rules = '[]';