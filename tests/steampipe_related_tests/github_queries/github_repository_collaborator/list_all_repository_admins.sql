select
  user_login,
  permission
from
  github_repository_collaborator
where
  repository_full_name = 'turbot/steampipe'
  and permission = 'ADMIN';