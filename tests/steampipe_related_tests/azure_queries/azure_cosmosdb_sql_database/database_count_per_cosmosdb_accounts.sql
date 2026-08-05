select
  account_name,
  count(name) as database_count
from
  azure_cosmosdb_sql_database
group by
  account_name;