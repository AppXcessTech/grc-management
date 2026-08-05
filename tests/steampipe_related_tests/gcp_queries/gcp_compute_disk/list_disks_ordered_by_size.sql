select
  name,
  size_gb
from
  gcp_compute_disk
order by
  size_gb desc;