select
  name,
  role_arn,
  status_recording,
  title
from
  aws_config_configuration_recorder
where
  not status_recording;