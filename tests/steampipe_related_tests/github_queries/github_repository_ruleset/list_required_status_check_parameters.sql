select
  id,
  name,
  r -> 'parameters' ->> 'Type' as type,
  r -> 'parameters' -> 'RequiredStatusChecksParameters' ->> 'required_status_checks' as required_status_checks
from
  github_repository_ruleset,
  jsonb_array_elements(rules) as r
where
  repository_full_name = 'pro-cloud-49/test-rule';