select
  name,
  id,
  cloud_environment,
  flexible_server_configurations,
  server_properties -> 'backup' ->> 'geoRedundantBackup',
  location
from
  azure_postgresql_flexible_server
where
  server_properties -> 'backup' ->> 'geoRedundantBackup' = 'Enabled';