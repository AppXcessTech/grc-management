select
  name,
  id,
  p ->> 'name' as name,
  r ->> 'paths' as paths,
  split_part(r ->> 'service', '/', 10) as service
from
  gcp_compute_url_map,
  jsonb_array_elements(path_matchers) as p,
  jsonb_array_elements(p -> 'pathRules') as r;