select
  name,
  value,
  visibility,
  created_at,
  updated_at
from
  github_actions_organization_variable
where
  organization = 'my-org';