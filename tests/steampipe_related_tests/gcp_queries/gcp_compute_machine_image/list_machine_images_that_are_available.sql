select
  name,
  id,
  description,
  creation_timestamp,
  status
from
  gcp_compute_machine_image
where
  status = 'READY';