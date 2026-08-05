select
  title,
  kms_master_key_id,
  sqs_managed_sse_enabled
from
  aws_sqs_queue
where
  sqs_managed_sse_enabled;