select
  name,
  id,
  status,
  autoscaling_policy_mode
from
  gcp_compute_node_group
where
  maintenance_policy = 'DEFAULT';