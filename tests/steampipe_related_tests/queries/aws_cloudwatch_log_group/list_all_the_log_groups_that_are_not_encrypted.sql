select
  name,
  kms_key_id,
  metric_filter_count,
  retention_in_days
from
  aws_cloudwatch_log_group
where
  kms_key_id is null;