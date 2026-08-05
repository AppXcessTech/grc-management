select
  name,
  id,
  b ->> 'balancingMode' as balancing_mode,
  split_part(b ->> 'group', '/', 10) as network_endpoint_groups
from
  gcp_compute_backend_service,
  jsonb_array_elements(backends) as b;