select
  name,
  r->>'id' as rule_id,
  r->>'type' as rule_type,
  r->>'parameters' as rule_parameters
from
  github_organization_ruleset,
  jsonb_array_elements(rules) as r
where
  organization = 'my-org'
  and name = 'my-ruleset';