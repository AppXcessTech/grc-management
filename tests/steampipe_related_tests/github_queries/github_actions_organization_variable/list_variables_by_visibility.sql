select
  name,
  value,
  visibility,
  selected_repositories_url
from
  github_actions_organization_variable
where
  organization = 'my-org'
order by
  visibility, name;