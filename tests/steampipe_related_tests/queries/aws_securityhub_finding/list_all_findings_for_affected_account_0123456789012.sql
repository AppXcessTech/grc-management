select
  title,
  f.severity ->> 'Original' as severity,
  r ->> 'Type' as resource_type,
  source_account_id
from
  aws_securityhub_finding as f,
  jsonb_array_elements(resources) r
where
  source_account_id = '0123456789012';