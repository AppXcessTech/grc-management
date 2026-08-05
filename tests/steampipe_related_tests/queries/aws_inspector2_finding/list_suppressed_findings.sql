select
  arn,
  status,
  type,
  resources,
  vulnerable_packages
from
  aws_inspector2_finding
where
  status = 'SUPPRESSED';