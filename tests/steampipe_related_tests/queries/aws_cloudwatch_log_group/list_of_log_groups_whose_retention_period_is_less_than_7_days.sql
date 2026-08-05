select
  name,
  retention_in_days
from
  aws_cloudwatch_log_group
where
  retention_in_days < 7;