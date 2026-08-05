select
  cluster_name,
  task_arn,
  a ->> 'Id' as attachment_id,
  a ->> 'Status' as attachment_status,
  a ->> 'Type' as attachment_type,
  jsonb_pretty(a -> 'Details') as attachment_details
from
  aws_ecs_task,
  jsonb_array_elements(attachments) as a;