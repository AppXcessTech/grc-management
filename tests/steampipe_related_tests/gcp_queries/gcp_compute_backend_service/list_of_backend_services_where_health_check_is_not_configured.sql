select
  name,
  id,
  self_link,
  health_checks
from
  gcp_compute_backend_service
where
  health_checks is null;