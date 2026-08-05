select
  name as user_name,
  inline_policies
from
  aws_iam_user
where
  inline_policies is not null;