select
  name as instance_name,
  i ->> 'name' as authorized_network_name,
  i ->> 'value' as authorized_network_value,
  ip_configuration ->> 'ipv4Enabled' as ipv4_enabled
from
  gcp_sql_database_instance,
  jsonb_array_elements(ip_configuration -> 'authorizedNetworks') as i;