select
  f.title,
  f.id,
  f.company_name,
  f.created_at,
  f.criticality,
  f.confidence
from
  aws_securityhub_finding as f,
  aws_securityhub_standards_control as c
where
  c.arn = f.standards_control_arn
and
  c.control_id = 'Config.1';