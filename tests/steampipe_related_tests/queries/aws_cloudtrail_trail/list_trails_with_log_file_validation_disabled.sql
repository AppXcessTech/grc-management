select
  name,
  arn,
  log_file_validation_enabled
from
  aws_cloudtrail_trail
where
  not log_file_validation_enabled;