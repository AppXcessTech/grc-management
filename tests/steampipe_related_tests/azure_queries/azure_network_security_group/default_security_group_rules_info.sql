select
  name,
  sg -> 'name' as sg_name,
  sg -> 'properties' ->> 'access' as access,
  sg -> 'properties' ->> 'description' as description,
  sg -> 'properties' ->> 'destinationPortRange' as destination_port_range,
  sg -> 'properties' ->> 'direction' as direction,
  sg -> 'properties' ->> 'priority' as priority,
  sg -> 'properties' ->> 'sourcePortRange' as source_port_range,
  sg -> 'properties' ->> 'protocol' as protocol
from
  azure_network_security_group
  cross join jsonb_array_elements(default_security_rules) as sg;