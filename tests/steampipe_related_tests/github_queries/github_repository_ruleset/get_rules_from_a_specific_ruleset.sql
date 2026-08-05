select
  name,
  r->>'id' as rule_id,
  r->>'type' as rule_type,
  r->>'parameters' as rule_parameters
from
  github_repository_ruleset,
  jsonb_array_elements(rules) as r
where
  repository_full_name = 'pro-cloud-49/test-rule'
  and name = 'test34';