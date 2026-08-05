select
  distinct i.instance_id,
  i.instance_state,
  i.instance_type,
  f.title,
  f.compliance_status,
  f.severity ->> 'Original' as severity_original
from
  aws_ec2_instance as i,
  aws_securityhub_finding as f,
  jsonb_array_elements(resources) as r
where
  compliance_status = 'FAILED'
and
  r ->> 'Type' = 'AwsEc2Instance'
and
  i.arn = r ->> 'Id';