select
  name,
  scheduling_config,
  zone
from
  gcp_compute_tpu
where
  scheduling_config is not null;