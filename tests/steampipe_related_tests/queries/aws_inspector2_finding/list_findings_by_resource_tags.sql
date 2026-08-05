select
  arn,
  finding_account_id,
  first_observed_at,
  fix_available,
  exploit_available,
  resource_tags
from
  aws_inspector2_finding
where
  resource_tags = '[{"key": "Name", "value": "Dev"}, {"key": "Name", "value": "Prod"}]';