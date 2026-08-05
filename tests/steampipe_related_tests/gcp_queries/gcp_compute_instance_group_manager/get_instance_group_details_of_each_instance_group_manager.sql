select
  m.name,
  g.name as group_name,
  g.size as group_size
from
  gcp_compute_instance_group_manager as m,
  gcp_compute_instance_group as g
where
  m.instance_group ->> 'name' = g.name;