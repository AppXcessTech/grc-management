select
  repository_full_name,
  id,
  name,
  os
from
  github_actions_repository_runner
where
  repository_full_name = 'turbot/steampipe' and os = 'macos';