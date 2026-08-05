select
  name,
  id,
  zone_name,
  disk_encryption_key_type
from
  gcp_compute_disk
where
  disk_encryption_key_type = 'Google managed';