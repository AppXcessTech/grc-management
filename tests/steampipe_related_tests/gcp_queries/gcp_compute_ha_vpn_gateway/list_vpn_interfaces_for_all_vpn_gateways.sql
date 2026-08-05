select
  name as vpn_gateway_name,
  i ->> 'id' as vpn_interface_id,
  i ->> 'ipAddress' as vpn_interface_ip_address
from
  gcp_compute_ha_vpn_gateway g,
  jsonb_array_elements(vpn_interfaces) i;