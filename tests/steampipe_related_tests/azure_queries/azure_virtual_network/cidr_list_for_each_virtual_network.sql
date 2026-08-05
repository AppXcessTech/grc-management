select
  name,
  jsonb_array_elements_text(address_prefixes) as address_block
from
  azure_virtual_network;