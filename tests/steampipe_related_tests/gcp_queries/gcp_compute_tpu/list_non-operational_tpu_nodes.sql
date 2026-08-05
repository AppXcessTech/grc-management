select
  name,
  state,
  health_description,
  zone
from
  gcp_compute_tpu
where
  state != 'READY';