select
  name,
  tags
from
  azure_cosmosdb_sql_database
where
  not tags :: JSONB ? 'application';