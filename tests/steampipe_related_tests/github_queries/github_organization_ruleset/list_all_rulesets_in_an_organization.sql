select
  name,
  enforcement,
  created_at
from
  github_organization_ruleset
where
  organization = 'my-org';