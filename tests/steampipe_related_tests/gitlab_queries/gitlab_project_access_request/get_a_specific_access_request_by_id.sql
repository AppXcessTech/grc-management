select
  username,
  requested_at
from
  gitlab_project_access_request
where
  project_id = 45453535
and
  id = 873;