select
  name,
  version,
  region,
  ssl_enforcement
from
  azure_mariadb_server
where
  ssl_enforcement = 'Enabled';