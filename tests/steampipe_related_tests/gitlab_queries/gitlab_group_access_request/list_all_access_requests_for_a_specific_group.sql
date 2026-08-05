select
  id,
  username,
  name,
  state,
  access_level,
  created_at,
  requested_at
from
  gitlab_group_access_request
where
  group_id = 14597683;