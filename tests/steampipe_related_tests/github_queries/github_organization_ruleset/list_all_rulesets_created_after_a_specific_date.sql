select
  name,
  created_at
from
  github_organization_ruleset
where
  organization = 'my-org'
  and created_at > '2023-01-01T00:00:00Z';