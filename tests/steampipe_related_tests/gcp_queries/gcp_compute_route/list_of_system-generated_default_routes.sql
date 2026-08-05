select
  name,
  dest_range,
  priority,
  next_hop_gateway
from
  gcp_compute_route
where
  priority = 1000
  and dest_range = '0.0.0.0/0';