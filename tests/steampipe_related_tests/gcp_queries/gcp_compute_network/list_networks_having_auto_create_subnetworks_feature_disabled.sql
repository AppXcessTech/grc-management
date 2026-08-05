select
  name,
  id,
  auto_create_subnetworks
from
  gcp_compute_network
where
  not auto_create_subnetworks;