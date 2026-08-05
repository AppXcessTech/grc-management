select
  id,
  company_name,
  created_at,
  confidence,
  compliance_status,
  product_name,
  product_arn
from
  aws_securityhub_finding
where
  created_at >= now() - interval '30d';