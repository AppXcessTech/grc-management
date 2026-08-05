select
  name,
  split_part(s ->> 'role', '/', 2) as role,
  entity
from
  gcp_service_account,
  jsonb_array_elements(iam_policy -> 'bindings') as s,
  jsonb_array_elements_text(s -> 'members') as entity
where
  entity = 'allUsers'
  or entity = 'allAuthenticatedUsers';