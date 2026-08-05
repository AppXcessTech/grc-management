select
  name,
  tags
from
  gcp_compute_instance
where
  tags -> 'application' is null;