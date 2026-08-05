select
  name,
  id,
  backup_retention_days
from
  azure_mysql_flexible_server
where
  backup_retention_days > 90;