select
  *
from
  gitlab_project_repository
where
  project_id = 123
and 
  type = 'tree'