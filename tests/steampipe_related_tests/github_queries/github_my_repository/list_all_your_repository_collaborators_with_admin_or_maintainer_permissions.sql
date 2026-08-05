select
  r.name_with_owner as repository_full_name,
  c.user_login,
  c.permission
from
  github_my_repository r
 ,github_repository_collaborator c
where
  r.name_with_owner = c.repository_full_name
and
  permission in ('ADMIN', 'MAINTAIN');