select
  name,
  slug,
  privacy,
  description
from
  github_team
where
  organization = 'turbot';