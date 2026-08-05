select
  name,
  owner_login,
  name_with_owner
from
  github_my_repository
order by
  name_with_owner;