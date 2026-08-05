select
  name,
  arn
from
  aws_iam_policy
where
  not is_aws_managed
  and path = '/turbot/';