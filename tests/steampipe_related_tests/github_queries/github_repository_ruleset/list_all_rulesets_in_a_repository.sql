select
  name,
  enforcement,
  created_at
from
  github_repository_ruleset
where
  repository_full_name = 'pro-cloud-49/test-rule';