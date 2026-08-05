select
  cluster_name,
  task_arn,
  protection ->> 'ProtectionEnabled' as protection_enabled,
  protection ->> 'ExpirationDate' as protection_expiration_date
from
  aws_ecs_task;