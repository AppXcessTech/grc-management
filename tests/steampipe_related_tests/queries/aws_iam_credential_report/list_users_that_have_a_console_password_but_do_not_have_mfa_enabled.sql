select
  user_name,
  mfa_active,
  password_enabled
from
  aws_iam_credential_report
where
  password_enabled
  and not mfa_active;