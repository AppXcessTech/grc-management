select
  name,
  id,
  split_part(i, '/', 11) as instance_name
from
  gcp_compute_target_pool,
  jsonb_array_elements_text(instances) as i;