select
  name,
  configurations ->> 'Name' as configuration_name,
  configurations -> 'ConfigurationProperties' ->> 'value' as configuration_value
from
  azure_postgresql_server,
  jsonb_array_elements(server_configurations) as configurations
where
  configurations ->> 'Name' = 'log_checkpoints'
  and configurations -> 'ConfigurationProperties' ->> 'value' = 'OFF';