select
  name,
  id,
  server_name,
  location,
  edition,
  transparent_data_encryption ->> 'status' as encryption_status
from
  azure_sql_database
where
  transparent_data_encryption ->> 'status' != 'Enabled';