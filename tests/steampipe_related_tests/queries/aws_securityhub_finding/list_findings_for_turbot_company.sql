select
  title,
  id,
  product_arn,
  product_name,
  company_name
from
  aws_securityhub_finding
where
  company_name = 'Turbot';