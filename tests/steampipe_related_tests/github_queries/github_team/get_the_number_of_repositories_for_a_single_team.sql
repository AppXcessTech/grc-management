select
  name,
  slug,
  repositories_total_count
from
  github_team
where
  organization = 'my_org'
  and slug = 'my_team';