select
  g.name,
  ins.name as instance_name,
  ins.status as instance_status
from
  gcp_compute_instance_group as g,
  jsonb_array_elements(instances) as i,
  gcp_compute_instance as ins
where
  (i ->> 'instance') = ins.self_link;