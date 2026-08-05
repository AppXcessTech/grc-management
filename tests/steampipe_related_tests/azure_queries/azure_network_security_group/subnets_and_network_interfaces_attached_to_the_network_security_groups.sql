select
  name,
  split_part(nic ->> 'id', '/', 9) network_interface,
  split_part(vn ->> 'id', '/', 9) virtual_network,
  split_part(vn ->> 'id', '/', 11) subnets
from
  azure_network_security_group
  cross join jsonb_array_elements(network_interfaces) as nic,
  jsonb_array_elements(subnets) as vn;