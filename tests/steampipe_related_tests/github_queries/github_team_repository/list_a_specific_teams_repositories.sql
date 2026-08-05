select
  organization,
  slug as team_slug,
  name as team_name,
  permission,
  primary_language ->> 'name' as language,
  fork_count,
  stargazer_count,
  license_info ->> 'spdx_id' as license,
  description,
  url
from
  github_team_repository
where
  organization = 'my_org'
  and slug = 'my-team';