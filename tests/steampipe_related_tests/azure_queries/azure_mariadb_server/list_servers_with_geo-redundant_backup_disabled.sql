select
  name,
  version,
  region,
  geo_redundant_backup_enabled
from
  azure_mariadb_server
where
  geo_redundant_backup_enabled = 'Disabled';