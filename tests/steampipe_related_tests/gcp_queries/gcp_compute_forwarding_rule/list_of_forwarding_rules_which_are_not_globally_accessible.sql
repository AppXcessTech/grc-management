select
  name,
  id,
  allow_global_access
from
  gcp_compute_forwarding_rule
where
  not allow_global_access;