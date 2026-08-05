select
  id,
  node_id,
  created_at,
  creator ->> 'login' as creator_login,
  commit_sha,
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
  repository_full_name in (select name_with_owner from github_my_repository);