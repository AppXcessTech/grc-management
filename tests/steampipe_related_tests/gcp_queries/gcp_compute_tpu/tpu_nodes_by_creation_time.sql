select
  name,
  create_time,
  zone
from
  gcp_compute_tpu
order by
  create_time;