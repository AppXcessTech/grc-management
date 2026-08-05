select
  name,
  id,
  location,
  ssl_enforcement
from
  azure_postgresql_server
where
  ssl_enforcement = 'Disabled';