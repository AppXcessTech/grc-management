select
  id,
  node_id,
  name
from
  github_repository_environment
where
  repository_full_name = 'turbot/steampipe';