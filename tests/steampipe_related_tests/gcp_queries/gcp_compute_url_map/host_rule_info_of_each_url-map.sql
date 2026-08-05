select
  name,
  id,
  p ->> 'hosts' as hosts,
  p ->> 'pathMatcher' as path_matcher
from
  gcp_compute_url_map,
  jsonb_array_elements(host_rules) as p;