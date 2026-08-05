select
  user_name
from
  aws_iam_credential_report
where
  password_enabled
  and password_last_used > (current_date - interval '90' day);