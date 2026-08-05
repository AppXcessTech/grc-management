select
  name,
  id,
  p ->> 'rangeName' as range_name,
  p ->> 'ipCidrRange' as ip_cidr_range
from
  gcp_compute_subnetwork,
  jsonb_array_elements(secondary_ip_ranges) as p;