select
  name,
  id,
  instance_can_ip_forward
from
  gcp_compute_instance_template
where
  instance_can_ip_forward;