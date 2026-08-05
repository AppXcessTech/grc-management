select
  g.name,
  g.id,
  g.location,
  t.node_type
from
  gcp_compute_node_group as g,
  gcp_compute_node_template as t
where
  g.node_template = t.self_link;