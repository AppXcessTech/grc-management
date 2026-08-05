select
  name,
  status
  last_resource_analyzed,
  last_resource_analyzed_at,
  tags
from
  aws_accessanalyzer_analyzer
where
  status = 'ACTIVE';