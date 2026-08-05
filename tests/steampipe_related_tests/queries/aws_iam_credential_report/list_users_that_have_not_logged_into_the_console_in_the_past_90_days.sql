select
  user_name,
  password_last_used,
  age(password_last_used)
from
  aws_iam_credential_report
where
  password_enabled
  and password_last_used <= (current_date - interval '90' day)
order by
  password_last_used;