select
  name,
  id,
  profile
from
  gcp_compute_ssl_policy
where
  profile = 'RESTRICTED';