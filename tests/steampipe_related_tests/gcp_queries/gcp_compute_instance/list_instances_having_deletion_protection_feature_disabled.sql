select
  name,
  deletion_protection
from
  gcp_compute_instance
where
  not deletion_protection;