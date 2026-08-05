select
  name as server_name,
  id as server_id,
  rules -> 'properties' ->> 'ignoreMissingVnetServiceEndpoint' as ignore_missing_vnet_service_endpoint,
  rules -> 'properties' ->> 'virtualNetworkSubnetId' as virtual_network_subnet_id
from
  azure_mysql_server,
  jsonb_array_elements(vnet_rules) as rules;