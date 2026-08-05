select
  id,
  iid,
  ref,
  sha,
  status,
  created_at,
  updated_at,
  user_id,
  user_username,
  environment_id,
  environment_name,
  deployable_id,
  deployable_status,
  deployable_stage,
  deployable_name,
  deployable_ref,
  deployable_commit_id,
  deployable_pipeline_id
from
  gitlab_project_deployment
where
  project_id = 14597683
and
  id = 1486132;