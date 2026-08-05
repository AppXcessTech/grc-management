select
  name,
  id,
  location,
  node_type
from
  gcp_compute_node_template
where
  node_type = 'n2-node-80-640';