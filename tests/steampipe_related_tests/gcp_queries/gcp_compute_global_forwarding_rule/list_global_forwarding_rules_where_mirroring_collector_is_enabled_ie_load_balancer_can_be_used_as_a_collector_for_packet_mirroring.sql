select
  name,
  id,
  is_mirroring_collector
from
  gcp_compute_global_forwarding_rule
where
  is_mirroring_collector;