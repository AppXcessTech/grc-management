select
  title,
  id,
  product_arn,
  product_name,
  workflow_status
from
  aws_securityhub_finding
where
  workflow_status = 'NOTIFIED';