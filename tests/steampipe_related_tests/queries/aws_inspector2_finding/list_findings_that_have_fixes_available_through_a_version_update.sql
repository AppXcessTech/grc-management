select
  arn,
  finding_account_id,
  first_observed_at,
  fix_available,
  exploit_available
from
  aws_inspector2_finding
where
  fix_available = 'YES';