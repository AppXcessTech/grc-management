select
  username,
  requested_at
from
  gitlab_group_access_request
where
  group_id = 14597683
and
  id = 132;