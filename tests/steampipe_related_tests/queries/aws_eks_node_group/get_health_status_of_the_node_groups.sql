select
  nodegroup_name,
  cluster_name,
  jsonb_pretty(health) as health
from
  aws_eks_node_group;