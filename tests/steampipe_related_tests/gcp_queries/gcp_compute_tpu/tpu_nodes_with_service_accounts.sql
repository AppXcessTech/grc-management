select
  name,
  service_account,
  zone
from
  gcp_compute_tpu
where
  service_account is not null;