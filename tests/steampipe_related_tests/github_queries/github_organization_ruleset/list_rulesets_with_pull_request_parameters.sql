select
  id,
  name,
  r -> 'parameters' ->> 'Type' as type,
  r -> 'parameters' -> 'PullRequestParameters' ->> 'require_code_owner_review' as require_code_owner_review,
  r -> 'parameters' -> 'PullRequestParameters' ->> 'required_approving_review_count' as required_approving_review_count
from
  github_organization_ruleset,
  jsonb_array_elements(rules) as r
where
  organization = 'my-org'
  and (r -> 'parameters' ->> 'Type') = 'PullRequestParameters';