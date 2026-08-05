select
  name as server_name,
  id as server_id,
  configurations ->> 'Name' as configuration_name,
  configurations -> 'ConfigurationProperties' ->> 'value' as value
from
  azure_mysql_flexible_server,
  jsonb_array_elements(flexible_server_configurations) as configurations
where
  configurations ->'ConfigurationProperties' ->> 'value' = 'FILE'
  and configurations ->> 'Name' = 'log_output';