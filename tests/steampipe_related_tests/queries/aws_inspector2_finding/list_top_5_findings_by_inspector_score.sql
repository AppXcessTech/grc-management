select
  arn,
  inspector_score,
  first_observed_at,
  last_observed_at
  inspector_score_details
from
  aws_inspector2_finding
order by
  inspector_score desc;