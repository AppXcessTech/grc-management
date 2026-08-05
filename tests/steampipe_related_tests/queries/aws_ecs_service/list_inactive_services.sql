select
  service_name,
  arn,
  status
from
  aws_ecs_service
where
  status = 'INACTIVE';