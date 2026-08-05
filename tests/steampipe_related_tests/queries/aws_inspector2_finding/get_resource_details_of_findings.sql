select
  f.arn as finding_arn,
  r ->> 'Id' as resource_id,
  r ->> 'Type' as resource_type,
  r ->> 'Details' as resource_details,
  r ->> 'Partition' as partition,
  r ->> 'Tags' as resource_tags
from
  aws_inspector2_finding as f,
  jsonb_array_elements(resources) as r;