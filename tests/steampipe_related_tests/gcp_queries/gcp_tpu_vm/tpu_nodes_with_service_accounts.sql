select
  name,
  service_account,
  zone
from
  gcp_tpu_vm
where
  service_account is not null;