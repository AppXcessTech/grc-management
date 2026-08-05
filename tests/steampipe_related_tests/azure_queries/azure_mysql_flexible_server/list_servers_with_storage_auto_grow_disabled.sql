select
  name,
  id,
  storage_auto_grow
from
  azure_mysql_flexible_server
where
  storage_auto_grow = 'Disabled';