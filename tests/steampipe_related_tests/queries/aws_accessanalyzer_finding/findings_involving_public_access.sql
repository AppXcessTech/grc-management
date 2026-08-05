select
  id,
  resource_type,
  access_analyzer_arn,
  status,
  is_public
from
  aws_accessanalyzer_finding
where
  is_public = true;