select
  name,
  id,
  enable_cdn
from
  gcp_compute_backend_bucket
where
  not enable_cdn;