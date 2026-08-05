select
  name,
  source_disk,
  self_link
from
  gcp_compute_snapshot
where
  kms_key_name is null;