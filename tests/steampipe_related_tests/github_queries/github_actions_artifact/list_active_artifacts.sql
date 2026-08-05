select
  id,
  node_id,
  name,
  archive_download_url,
  expired
from
  github_actions_artifact
where
  repository_full_name = 'turbot/steampipe' and not expired;