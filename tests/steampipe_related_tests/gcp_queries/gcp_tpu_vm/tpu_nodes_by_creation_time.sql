select
  name,
  create_time,
  zone
from
  gcp_tpu_vm
order by
  create_time;