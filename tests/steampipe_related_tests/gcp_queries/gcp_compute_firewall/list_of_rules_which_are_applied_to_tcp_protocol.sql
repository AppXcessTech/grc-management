select
  name,
  id,
  p ->> 'IPProtocol' as ip_protocol,
  p ->> 'ports' as ports
from
  gcp_compute_firewall,
  jsonb_array_elements(allowed) as p
where
  p ->> 'IPProtocol' = 'tcp';