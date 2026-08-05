select
  title,
  message_retention_seconds
from
  aws_sqs_queue
where
  message_retention_seconds < '604800';