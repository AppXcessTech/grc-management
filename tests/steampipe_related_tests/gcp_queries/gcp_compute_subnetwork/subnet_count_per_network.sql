select
  network,
  count(*) as subnet_count
from
  gcp_compute_subnetwork
group by
  network;