select
  id,
  name,
  r -> 'parameters' ->> 'Type' as type,
  r -> 'parameters' -> 'RequiredStatusChecksParameters' ->> 'required_status_checks' as required_status_checks
from
  github_organization_ruleset,
  jsonb_array_elements(rules) as r
where
  organization = 'my-org'
  and (r -> 'parameters' ->> 'Type') = 'RequiredStatusChecksParameters';