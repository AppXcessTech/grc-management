select
  t.name,
  t.id
from
  gcp_compute_node_template as t
left join
  gcp_compute_node_group as g on g.node_template = t.self_link
where
  g is null;