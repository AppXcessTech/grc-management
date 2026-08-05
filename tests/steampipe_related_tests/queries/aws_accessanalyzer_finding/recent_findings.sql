select
  id,
  resource,
  status,
  analyzed_at
from
  aws_accessanalyzer_finding
where
  analyzed_at > current_date - interval '30 days';