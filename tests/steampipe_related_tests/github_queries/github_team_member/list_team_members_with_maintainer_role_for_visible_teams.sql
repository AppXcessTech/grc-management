select
  t.organization as organization,
  t.name as team_name,
  t.slug as team_slug,
  t.privacy as team_privacy,
  t.description as team_description,
  tm.login as member_login,
  tm.role as member_role,
  tm.status as member_status
from
  github_team as t,
  github_team_member as tm
where
  t.organization = tm.organization
  and t.slug = tm.slug
  and tm.role = 'MAINTAINER';