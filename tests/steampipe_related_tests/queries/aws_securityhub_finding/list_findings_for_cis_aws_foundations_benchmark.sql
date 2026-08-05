select
  title,
  id,
  company_name,
  created_at,
  criticality,
  confidence
from
  aws_securityhub_finding
where
  standards_control_arn like '%cis-aws-foundations-benchmark%';