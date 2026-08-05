select
  name,
  region_name
from
  gcp_compute_disk
where
  location_type = 'REGIONAL';