select
  title,
  kms_master_key_id,
  sqs_managed_sse_enabled
from
  aws_sqs_queue
where
  kms_master_key_id is null
  and not sqs_managed_sse_enabled;