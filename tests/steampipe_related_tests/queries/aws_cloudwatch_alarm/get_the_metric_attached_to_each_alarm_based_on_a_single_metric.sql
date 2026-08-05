select
  name,
  metric_name,
  namespace,
  period,
  statistic,
  dimensions
from
  aws_cloudwatch_alarm
where
  metric_name is not null;