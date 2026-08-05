select
  name,
  id,
  location,
  geo_redundant_backup
from
  azure_postgresql_server
where
  geo_redundant_backup = 'Disabled';