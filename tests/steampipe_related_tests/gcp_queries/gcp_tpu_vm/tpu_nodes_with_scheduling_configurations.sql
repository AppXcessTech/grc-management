select
  name,
  scheduling_config,
  zone
from
  gcp_tpu_vm
where
  scheduling_config is not null;