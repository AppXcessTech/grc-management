select
  name,
  id,
  direction,
  allowed,
  denied
from
  gcp_compute_firewall
where
  direction = 'EGRESS';