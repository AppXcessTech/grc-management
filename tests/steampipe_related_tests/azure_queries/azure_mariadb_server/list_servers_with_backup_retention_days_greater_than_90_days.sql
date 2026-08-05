select
  name,
  version,
  region,
  backup_retention_days
from
  azure_mariadb_server
where
  backup_retention_days > 90;