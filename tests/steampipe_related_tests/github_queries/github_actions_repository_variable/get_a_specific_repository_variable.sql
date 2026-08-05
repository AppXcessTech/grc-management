select
  name,
  value,
  created_at,
  updated_at
from
  github_actions_repository_variable
where
  repository_full_name = 'turbot/steampipe'
  and name = 'MY_VARIABLE';