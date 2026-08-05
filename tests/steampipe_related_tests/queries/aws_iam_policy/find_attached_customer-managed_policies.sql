select
  name,
  arn,
  permissions_boundary_usage_count
from
  aws_iam_policy
where
  is_attached;