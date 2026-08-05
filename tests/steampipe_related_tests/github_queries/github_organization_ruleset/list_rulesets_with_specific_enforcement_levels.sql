select
  name,
  enforcement
from
  github_organization_ruleset
where
  organization = 'my-org'
  and enforcement = 'ACTIVE';