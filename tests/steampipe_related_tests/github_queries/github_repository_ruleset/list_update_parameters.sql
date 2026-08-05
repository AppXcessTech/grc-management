select
  id,
  name,
  r -> 'parameters' ->> 'Type' as type,
  r -> 'parameters' -> 'UpdateParameters' ->> 'update_allows_fetch_and_merge' as update_allows_fetch_and_merge
from
  github_repository_ruleset,
  jsonb_array_elements(rules) as r
where
  repository_full_name = 'pro-cloud-49/test-rule'
and
  (r -> 'parameters' ->> 'Type') = 'UpdateParameters';