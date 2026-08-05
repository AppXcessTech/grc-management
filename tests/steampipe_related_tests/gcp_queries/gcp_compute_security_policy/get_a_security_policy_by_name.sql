select
  name,
  id,
  description,
  rules,
  labels,
  project
from
  gcp_compute_security_policy
where
  name = 'my-security-policy';