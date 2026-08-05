select
  arn,
  actions_enabled,
  alarm_actions
from
  aws_cloudwatch_alarm
where
  actions_enabled;