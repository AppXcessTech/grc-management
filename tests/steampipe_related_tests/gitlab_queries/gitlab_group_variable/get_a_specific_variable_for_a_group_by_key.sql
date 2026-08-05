select
  key,
  value,
  variable_type,
  environment_scope,
  masked,
  protected,
  raw
from 
  gitlab_group_variable
where
  project_id = 42
and
  key = 'VARIABLE_NAME';