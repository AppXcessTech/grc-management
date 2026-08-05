select
  name,
  id,
  connection_draining_timeout_sec
from
  gcp_compute_backend_service
where
  connection_draining_timeout_sec < 300;