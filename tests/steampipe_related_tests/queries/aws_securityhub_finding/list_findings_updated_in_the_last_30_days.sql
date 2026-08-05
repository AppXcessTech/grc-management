select
  title,
  product_arn,
  product_name,
  updated_at
from
  aws_securityhub_finding
where
   updated_at >= now() - interval '30' day;