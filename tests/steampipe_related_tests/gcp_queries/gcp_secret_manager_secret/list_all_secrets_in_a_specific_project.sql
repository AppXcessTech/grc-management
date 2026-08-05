select
  name,
  project,
  create_time,
  expire_time
from
  gcp_secret_manager_secret
where
  project = 'my-gcp-project';