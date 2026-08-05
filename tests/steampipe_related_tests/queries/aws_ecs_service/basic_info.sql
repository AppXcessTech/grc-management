select
  service_name,
  arn,
  cluster_arn,
  task_definition,
  status
from
  aws_ecs_service;