select
  a.title as autoscaler_name,
  g.name as instance_group_name,
  g.description as instance_group_description,
  g.size as instance_group_size
from
  gcp_compute_instance_group g,
  gcp_compute_autoscaler a
where
  g.name = split_part(a.target, 'instanceGroupManagers/', 2);