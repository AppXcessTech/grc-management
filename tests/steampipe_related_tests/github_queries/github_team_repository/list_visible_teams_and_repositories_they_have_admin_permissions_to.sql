select
  organization,
  slug as team_slug,
  name as name,
  description,
  permission,
  is_fork,
  is_private,
  is_archived,
  primary_language ->> 'name' as language
from
  github_team_repository
where
  organization = 'my_org'
  and slug = 'my-team'
  and permission = 'ADMIN';