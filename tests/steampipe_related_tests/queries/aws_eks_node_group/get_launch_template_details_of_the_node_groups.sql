select
  nodegroup_name,
  cluster_name,
  jsonb_pretty(launch_template) as launch_template
from
  aws_eks_node_group;