select
  (expire_passwords and max_password_age <= 90)
from
  aws_iam_account_password_policy;