select
  network_tier,
  count(*)
from
  gcp_compute_address
group by
  network_tier
order by network_tier;