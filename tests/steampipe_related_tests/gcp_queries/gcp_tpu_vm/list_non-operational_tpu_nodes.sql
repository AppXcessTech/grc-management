select
  name,
  state,
  health_description,
  zone
from
  gcp_tpu_vm
where
  state != 'READY';