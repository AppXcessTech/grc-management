select
  name,
  id,
  node_type
from
  gcp_compute_node_template
where
  cpu_overcommit_type = 'ENABLED';