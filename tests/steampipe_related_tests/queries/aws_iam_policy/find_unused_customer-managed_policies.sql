select
  name,
  attachment_count,
  permissions_boundary_usage_count
from
  aws_iam_policy
where
  not is_aws_managed
  and not is_attached
  and permissions_boundary_usage_count = 0;