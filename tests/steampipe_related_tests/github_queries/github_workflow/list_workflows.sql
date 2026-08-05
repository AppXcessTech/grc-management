select
  repository_full_name,
  name,
  path,
  node_id,
  state,
  url
from
  github_workflow
where
  repository_full_name = 'turbot/steampipe';