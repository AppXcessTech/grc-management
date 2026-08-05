select
  name,
  id,
  status,
  autoscaling_policy_mode
from
  gcp_compute_node_group
where
  autoscaling_policy_mode <> 'ON';