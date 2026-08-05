select
  account_name,
  count(name) as database_count
from
  azure_cosmosdb_mongo_database
group by
  account_name;