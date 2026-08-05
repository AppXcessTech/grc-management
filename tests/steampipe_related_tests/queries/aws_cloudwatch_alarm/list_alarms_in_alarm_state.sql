select
  name,
  arn,
  state_value,
  state_reason
from
  aws_cloudwatch_alarm
where
 state_value = 'ALARM';