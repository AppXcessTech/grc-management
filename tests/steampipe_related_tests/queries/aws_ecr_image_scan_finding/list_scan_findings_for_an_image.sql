select
  repository_name,
  image_tag,
  name,
  severity,
  description,
  attributes,
  uri,
  image_scan_status,
  image_scan_completed_at,
  vulnerability_source_updated_at
from
  aws_ecr_image_scan_finding
where
  repository_name = 'my-repo'
  and image_tag = 'my-image-tag';