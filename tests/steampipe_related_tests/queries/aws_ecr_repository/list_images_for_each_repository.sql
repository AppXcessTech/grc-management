select
  r.repository_name as repository_name,
  i.image_digest as image_digest,
  i.image_tags as image_tags,
  i.image_pushed_at as image_pushed_at,
  i.image_size_in_bytes as image_size_in_bytes,
  i.last_recorded_pull_time as last_recorded_pull_time,
  i.registry_id as registry_id,
  i.image_scan_status as image_scan_status
from
  aws_ecr_repository as r,
  aws_ecr_image as i
where
  r.repository_name = i.repository_name;