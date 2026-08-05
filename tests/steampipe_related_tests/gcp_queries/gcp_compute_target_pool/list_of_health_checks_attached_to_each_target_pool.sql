select
  name,
  id,
  split_part(h, '/', 10) as health_check
from
  gcp_compute_target_pool,
  jsonb_array_elements_text(health_checks) as h;