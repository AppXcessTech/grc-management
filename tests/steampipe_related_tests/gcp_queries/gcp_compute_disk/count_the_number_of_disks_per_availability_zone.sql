select
  zone_name,
  count(*)
from
  gcp_compute_disk
group by
  zone_name
order by
  count desc;