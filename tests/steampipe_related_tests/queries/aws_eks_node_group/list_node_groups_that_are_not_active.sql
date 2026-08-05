select
  nodegroup_name,
  arn,
  created_at,
  cluster_name,
  status
from
  aws_eks_node_group
where
  status <> 'ACTIVE';