select
  name,
  id,
  instance_machine_type
from
  gcp_compute_instance_template
where
  instance_machine_type = 'c2-standard-4';