select
  name,
  id,
  self_link,
  status,
  total_storage_bytes
from
  gcp_compute_machine_image
order by
  total_storage_bytes asc
limit 5;