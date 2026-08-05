select
  name,
  tags,
  zone
from
  gcp_compute_tpu
where
  tags is not null;