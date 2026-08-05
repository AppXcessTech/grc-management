select
  name,
  count(d) as num_subnets
from
  gcp_compute_network as i,
  jsonb_array_elements(subnetworks) as d
group by
  name;