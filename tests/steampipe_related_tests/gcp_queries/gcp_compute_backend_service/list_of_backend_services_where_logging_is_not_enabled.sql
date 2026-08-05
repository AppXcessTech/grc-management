select
  name,
  id,
  log_config_enable
from
  gcp_compute_backend_service
where
   not log_config_enable;