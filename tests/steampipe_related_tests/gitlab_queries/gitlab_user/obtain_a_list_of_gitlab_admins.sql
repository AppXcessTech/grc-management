select
  username,
  name,
  state,
  email
from
  gitlab_user
where
  is_admin = true;