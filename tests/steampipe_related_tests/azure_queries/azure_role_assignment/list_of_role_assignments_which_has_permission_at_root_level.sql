select
  name,
  id,
  scope
from
  azure_role_assignment
where
  scope = '/';