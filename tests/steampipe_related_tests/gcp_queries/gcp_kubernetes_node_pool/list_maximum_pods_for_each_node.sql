select
  name,
  cluster_name,
  max_pods_constraint ->> 'maxPodsPerNode' as max_mods_per_node
from
  gcp_kubernetes_node_pool;