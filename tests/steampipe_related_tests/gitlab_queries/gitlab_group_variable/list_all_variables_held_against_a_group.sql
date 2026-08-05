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
  group_id = 42;