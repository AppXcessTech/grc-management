select
  name,
  id,
  users
from
  gcp_compute_disk
where
  users is null;