select
  c.name as connector_name,
  c.location,
  c.network,
  s ->> 'name' as subnet_name,
  s ->> 'ipCidrRange' as subnet_ip_range
from
  gcp_vpc_access_connector c,
  jsonb_array_elements(c.subnet) as s;