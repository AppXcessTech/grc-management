select
  name,
  id,
  server_name,
  location,
  edition,
  status
from
  azure_sql_database
where
  status != 'Online';