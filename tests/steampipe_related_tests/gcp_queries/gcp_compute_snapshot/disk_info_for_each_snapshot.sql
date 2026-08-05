select
  s.name as snapshot_name,
  d.name as disk_name,
  d.size_gb as disk_size,
  d.type_name as disk_type,
  d.location_type
from
  gcp_compute_snapshot as s
  join gcp_compute_disk as d on s.source_disk = d.self_link;