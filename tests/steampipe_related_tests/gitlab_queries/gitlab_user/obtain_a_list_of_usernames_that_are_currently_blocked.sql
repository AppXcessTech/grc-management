select
  username,
  state
from
  gitlab_user
where
  state = 'blocked';