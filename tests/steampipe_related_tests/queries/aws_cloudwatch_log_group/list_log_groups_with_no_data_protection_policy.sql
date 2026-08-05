select
  arn,
  name,
  creation_time
from
  aws_cloudwatch_log_group
where
  data_protection_policy is null;