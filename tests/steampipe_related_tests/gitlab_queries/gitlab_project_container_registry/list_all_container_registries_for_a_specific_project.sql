select
  id,
  name,
  path,
  location,
  created_at,
  cleanup_policy_started_at
from
  gitlab_project_container_registry
where
  project_id = 45453535;