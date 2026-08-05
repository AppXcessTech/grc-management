select
  r.repository_name as repository_name,
  i.image_digest as image_digest,
  i.image_scan_status as image_scan_status
from
  aws_ecr_repository as r,
  aws_ecr_image as i
where
  r.repository_name = i.repository_name
  and i.image_scan_status ->> 'Status' = 'FAILED';