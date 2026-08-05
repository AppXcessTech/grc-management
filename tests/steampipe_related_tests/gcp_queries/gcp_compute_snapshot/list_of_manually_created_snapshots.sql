select
  name,
  source_disk_name,
  auto_created
from
  gcp_compute_snapshot
where
  not auto_created;