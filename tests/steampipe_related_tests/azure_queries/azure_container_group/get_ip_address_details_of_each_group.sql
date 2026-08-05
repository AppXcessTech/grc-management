select
  name,
  ip_address -> 'Ports' as ports,
  ip_address ->> 'Type' as ip_address_type,
  ip_address ->> 'IP' as ip,
  ip_address ->> 'DNSNameLabel' as dns_name_label,
  ip_address ->> 'Fqdn' as fqdn
from
  azure_container_group;