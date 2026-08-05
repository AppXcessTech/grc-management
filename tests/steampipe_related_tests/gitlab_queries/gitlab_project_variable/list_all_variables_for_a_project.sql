select
  key,
  value,
  variable_type,
  environment_scope,
  masked,
  protected,
  raw
from 
  gitlab_project_variable
where
  project_id = 173;