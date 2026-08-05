select
  name,
  id,
  location_type
from
  gcp_compute_url_map
where
  location_type = 'GLOBAL';