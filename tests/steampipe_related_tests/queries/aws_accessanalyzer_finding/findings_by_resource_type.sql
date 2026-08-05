select
  resource_type,
  count(*) as findings_count
from
  aws_accessanalyzer_finding
group by
  resource_type;