select
  name,
  cidr_block,
  region,
  resource_group
from
  azure_virtual_network
  cross join jsonb_array_elements_text(address_prefixes) as cidr_block
where
  not cidr_block :: cidr = '10.0.0.0/16'
  and not cidr_block :: cidr = '192.168.0.0/16'
  and not cidr_block :: cidr = '172.16.0.0/12';