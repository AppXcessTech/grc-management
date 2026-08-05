select
  id,
  name,
  config -> 'id' as config_id,
  config -> 'name' as config_name,
  jsonb_pretty(config -> 'properties' -> 'publicIPAddress') as config_public_ip_address,
  config -> 'properties' -> 'privateIPAllocationMethod' as config_private_ip_allocation_method
from
  azure_application_gateway,
  jsonb_array_elements(frontend_ip_configurations) as config;