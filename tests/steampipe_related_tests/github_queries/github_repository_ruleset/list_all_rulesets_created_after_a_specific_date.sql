select
  name,
  created_at
from
  github_repository_ruleset
where
  repository_full_name = 'pro-cloud-49/test-rule'
  and created_at > '2023-01-01T00:00:00Z';