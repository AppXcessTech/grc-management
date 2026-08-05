select
  id,
  username,
  name,
  state,
  access_level,
  created_at,
  requested_at
from
  gitlab_project_access_request
where
  project_id = 45453535;