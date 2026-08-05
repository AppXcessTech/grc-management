select
  repository_full_name,
  name,
  value,
  updated_at
from
  github_actions_repository_variable
where
  repository_full_name = 'turbot/steampipe'
  and updated_at > now() - interval '7 days'
order by
  updated_at desc;