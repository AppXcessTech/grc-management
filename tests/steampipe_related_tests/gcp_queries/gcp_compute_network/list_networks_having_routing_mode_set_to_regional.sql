select
  name,
  id,
  routing_mode
from
  gcp_compute_network
where
  routing_mode = 'REGIONAL';