select
  name,
  create_date
from
  aws_iam_role
where
  inline_policies is not null;