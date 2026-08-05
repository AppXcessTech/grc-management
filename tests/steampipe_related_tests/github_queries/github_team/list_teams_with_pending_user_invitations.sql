select
  name,
  slug,
  invitations_total_count
from
  github_team
where
  organization = 'turbot'
  and invitations_total_count > 0;