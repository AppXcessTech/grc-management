select
  title,
  arn,
  severity
from
  aws_inspector2_finding
where
  last_observed_at >= now() - interval '10' day;