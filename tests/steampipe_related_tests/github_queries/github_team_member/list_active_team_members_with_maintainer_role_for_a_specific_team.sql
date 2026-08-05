select
  organization,
  slug as team_slug,
  login,
  role,
  status
from
  github_team_member
where
  organization = 'my_org'
  and slug = 'my-team'
  and role = 'MAINTAINER';