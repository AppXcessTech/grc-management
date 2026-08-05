select
  name,
  status ->> 'LastStatus' as last_status,
  status ->> 'LastStatusChangeTime' as last_status_change_time,
  status ->> 'LastErrorCode' as last_error_code,
  status ->> 'LastErrorMessage' as last_error_message
from
  aws_config_configuration_recorder
where
  status ->> 'LastStatus' = 'FAILURE';