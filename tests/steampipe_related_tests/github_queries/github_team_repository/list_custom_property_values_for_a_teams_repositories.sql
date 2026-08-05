select
  organization,
  slug,
  name,
  custom_properties
from
  github_team_repository
where
  organization = 'my_org'
  and slug = 'my-team';