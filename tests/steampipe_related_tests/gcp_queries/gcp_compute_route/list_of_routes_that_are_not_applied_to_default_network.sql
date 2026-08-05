select
  name,
  id,
  network_name as network
from
  gcp_compute_route
where
  network_name <> 'default';