select
  source_disk_name,
  count(*) as snapshot_count
from
  gcp_compute_snapshot
group by
  source_disk_name;