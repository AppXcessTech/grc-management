select
  name,
  symptoms,
  health_description,
  zone
from
  gcp_compute_tpu
where
  symptoms is not null;