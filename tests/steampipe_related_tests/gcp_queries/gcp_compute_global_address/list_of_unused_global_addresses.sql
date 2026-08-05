select
  name,
  address,
  status
from
  gcp_compute_global_address
where
  status <> 'IN_USE';