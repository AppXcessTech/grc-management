select
  id,
  name,
  r -> 'parameters' ->> 'Type' as type,
  r -> 'parameters' -> 'PullRequestParameters' ->> 'require_code_owner_review' as require_code_owner_review,
  r -> 'parameters' -> 'PullRequestParameters' ->> 'required_approving_review_count' as required_approving_review_count
from
  github_repository_ruleset,
  jsonb_array_elements(rules) as r
where
  repository_full_name = 'pro-cloud-49/test-rule'
and
  (r -> 'parameters' ->> 'Type') = 'PullRequestParameters';