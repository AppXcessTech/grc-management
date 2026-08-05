select
  name,
  description,
  permissions_boundary_arn,
  permissions_boundary_type
from
  aws_iam_role;