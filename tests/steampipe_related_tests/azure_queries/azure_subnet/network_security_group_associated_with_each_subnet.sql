select
  name subnet_name,
  virtual_network_name,
  split_part(network_security_group_id, '/', 9) as network_security_name
from
  azure_subnet;