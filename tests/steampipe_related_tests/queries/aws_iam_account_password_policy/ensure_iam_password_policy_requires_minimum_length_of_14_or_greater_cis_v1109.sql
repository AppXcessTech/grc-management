select
  minimum_password_length >= 14
from
  aws_iam_account_password_policy;