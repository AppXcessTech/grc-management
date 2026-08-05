select
  name,
  self_link,
  status
from
  gcp_compute_resource_policy
where
  status = 'INVALID';