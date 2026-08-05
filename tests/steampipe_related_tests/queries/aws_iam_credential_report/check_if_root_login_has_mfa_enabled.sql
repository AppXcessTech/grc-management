select
  user_name,
  mfa_active
from
  aws_iam_credential_report
where
  user_name = '<root_account>';