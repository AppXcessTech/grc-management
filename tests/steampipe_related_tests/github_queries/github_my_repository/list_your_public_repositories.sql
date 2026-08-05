select
  name,
  is_private,
  visibility,
  owner_login
from
  github_my_repository
where
  not is_private;