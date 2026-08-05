select
  name,
  description,
  role_name,
  role_type,
  title
from
  azure_role_definition
where
  role_type = 'CustomRole';