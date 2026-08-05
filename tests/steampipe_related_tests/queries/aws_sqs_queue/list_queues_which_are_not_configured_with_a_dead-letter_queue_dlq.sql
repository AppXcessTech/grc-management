select
  title,
  redrive_policy
from
  aws_sqs_queue
where
  redrive_policy is null;