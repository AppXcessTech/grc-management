select
  zone,
  count(*) as tpu_count,
  array_agg(name) as tpu_names
from
  gcp_compute_tpu
group by
  zone
order by
  tpu_count desc;