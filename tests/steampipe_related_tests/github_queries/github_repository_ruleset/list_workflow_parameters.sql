select
  id,
  name,
  r -> 'parameters' ->> 'Type' as type,
  r -> 'parameters' -> 'WorkflowsParameters' ->> 'workflows' as workflows
from
  github_repository_ruleset,
  jsonb_array_elements(rules) as r
where
  repository_full_name = 'pro-cloud-49/test-rule'
and
  (r -> 'parameters' ->> 'Type') = 'WorkflowsParameters';