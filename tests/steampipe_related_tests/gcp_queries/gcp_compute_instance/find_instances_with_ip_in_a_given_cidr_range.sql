select
  name,
  nic ->> 'networkIP' as ip_address
from
  gcp_compute_instance as i,
  jsonb_array_elements(network_interfaces) as nic
where
  (nic ->> 'networkIP') :: inet <<= '10.128.0.0/16' ;