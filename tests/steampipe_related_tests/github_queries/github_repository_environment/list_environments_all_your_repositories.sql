select
  id,
  node_id,
  name
from
  github_repository_environment
where
  repository_full_name in (select name_with_owner from github_my_repository);