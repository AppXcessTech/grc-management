select
  id,
  node_id,
  commit_sha,
  created_at,
  creator ->> 'login' as creator_login,
  description,
  environment,
  latest_status,
  payload,
  ref ->> 'prefix' as ref_prefix,
  ref ->> 'name' as ref_name,
  state,
  task,
  updated_at
from
  github_repository_deployment
where
  repository_full_name = 'turbot/steampipe';