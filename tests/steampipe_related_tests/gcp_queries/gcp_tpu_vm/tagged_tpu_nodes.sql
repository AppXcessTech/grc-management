select
  name,
  tags,
  zone
from
  gcp_tpu_vm
where
  tags is not null;