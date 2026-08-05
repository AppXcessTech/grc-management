select
  repository_full_name,
  count(*) as variable_count
from
  github_actions_repository_variable
where
  repository_full_name in ('turbot/steampipe', 'turbot/steampipe-plugin-sdk')
group by
  repository_full_name;