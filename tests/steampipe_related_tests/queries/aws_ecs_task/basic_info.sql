select
  cluster_name,
  desired_status,
  launch_type,
  task_arn
from
  aws_ecs_task;