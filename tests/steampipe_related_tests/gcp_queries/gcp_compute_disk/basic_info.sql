select
  name,
  id,
  size_gb as disk_size_in_gb,
  type_name,
  zone_name,
  region_name,
  location_type
from
  gcp_compute_disk;