select
  name,
  id,
  creation_timestamp,
  description,
  self_link
from
  gcp_compute_security_policy
where
  filter = 'id = 4811866613213140474 AND description = "Default security policy for: tet5s"';