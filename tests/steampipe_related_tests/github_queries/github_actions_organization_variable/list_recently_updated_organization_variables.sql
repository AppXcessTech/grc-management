select
  organization,
  name,
  value,
  visibility,
  updated_at
from
  github_actions_organization_variable
where
  organization = 'my-org'
  and updated_at > now() - interval '7 days'
order by
  updated_at desc;