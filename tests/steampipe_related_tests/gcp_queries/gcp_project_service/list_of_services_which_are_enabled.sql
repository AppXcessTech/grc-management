select
  name,
  state
from
  gcp_project_service
where
  state = 'ENABLED';