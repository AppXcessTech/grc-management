select
  p.name as policy_name,
  i.name,
  p.instance_schedule_policy
from
  gcp_compute_resource_policy as p
  join gcp_compute_instance as i on i.resource_policies ?| array[p.self_link]
where
  p.instance_schedule_policy is not null;