select
  name,
  description,
  stage
from
  gcp_iam_role
where
  stage = 'BETA';