select
  cluster_arn,
  status
from
  aws_ecs_cluster
where
  status = 'FAILED';