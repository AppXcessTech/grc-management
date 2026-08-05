select
  title,
  fifo_queue
from
  aws_sqs_queue
where
  fifo_queue;