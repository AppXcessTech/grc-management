select
  name,
  project,
  expire_time
from
  gcp_secret_manager_secret
where
  expire_time < now() + interval '30 days';