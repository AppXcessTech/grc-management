select
  name,
  role_name,
  scope
from
  azure_role_definition,
  jsonb_array_elements_text(assignable_scopes) as scope
where
  scope = '/';