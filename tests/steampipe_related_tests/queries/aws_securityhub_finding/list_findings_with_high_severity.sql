select
  title,
  product_arn,
  product_name,
  severity ->> 'Original' as severity_original
from
  aws_securityhub_finding
where
  severity ->> 'Original' = 'HIGH';