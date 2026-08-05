select
  user_name
from
  aws_iam_credential_report
where
  password_status = 'never_used';