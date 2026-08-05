select
  name,
  description,
  stage
from
  gcp_iam_role
where
  is_gcp_managed = false;