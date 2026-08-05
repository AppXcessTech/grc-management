select
  title,
  product_arn,
  product_name,
  compliance ->> 'Status' as compliance_status,
  compliance ->> 'StatusReasons' as compliance_status_reasons
from
  aws_securityhub_finding
where
  compliance ->> 'Status' = 'FAILED';