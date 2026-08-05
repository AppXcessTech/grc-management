select
  f.repository_name,
  f.image_tag,
  f.name,
  f.severity,
  jsonb_pretty(f.attributes) as attributes
from
  (
    select
      repository_name,
      jsonb_array_elements_text(image_tags) as image_tag
    from
      aws_ecr_image as i
    where
      i.image_pushed_at > now() - interval '24' hour
  )
  images
  left outer join
    aws_ecr_image_scan_finding as f
    on images.repository_name = f.repository_name
    and images.image_tag = f.image_tag;