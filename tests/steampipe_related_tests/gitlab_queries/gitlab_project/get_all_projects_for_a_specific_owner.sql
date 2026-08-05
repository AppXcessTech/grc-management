select
  id,
  namespace_full_path as project
from
  gitlab_project
where
  owner_username = 'test';