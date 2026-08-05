select
  distinct r ->> 'Id' as resource_arn,
  r ->> 'Type' as resource_type,
  f.title,
  f.compliance_status,
  f.severity ->> 'Original' as severity_original
from
  aws_securityhub_finding as f,
  jsonb_array_elements(resources) as r
where
  f.compliance_status = 'FAILED'
and
  standards_control_arn like '%cis-aws-foundations-benchmark%';