select
  location,
  count(*)
from
  gcp_compute_node_template
group by
  location;