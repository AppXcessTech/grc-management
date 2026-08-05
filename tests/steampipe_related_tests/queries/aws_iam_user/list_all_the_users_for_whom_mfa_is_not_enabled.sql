select
  name,
  user_id,
  mfa_enabled
from
  aws_iam_user
where
  not mfa_enabled;