select
  name,
  id,
  load_balancing_scheme
from
  gcp_compute_forwarding_rule
where
  load_balancing_scheme = 'EXTERNAL';