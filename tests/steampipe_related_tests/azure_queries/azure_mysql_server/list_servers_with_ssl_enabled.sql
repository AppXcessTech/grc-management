select
  name,
  id,
  location,
  ssl_enforcement
from
  azure_mysql_server
where
  ssl_enforcement = 'Enabled';