select
  name,
  symptoms,
  health_description,
  zone
from
  gcp_tpu_vm
where
  symptoms is not null;