select
  name,
  value,
  visibility,
  created_at,
  updated_at
from
  github_actions_organization_variable
where
  organization = 'my-org'
  and name = 'MY_VARIABLE';