select
  service_name,
  arn,
  launch_type,
  platform_version
from
  aws_ecs_service
where
  launch_type = 'FARGATE'
  and platform_version is not null;