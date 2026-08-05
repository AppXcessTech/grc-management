select
  entity,
  p ->> 'role' as role
from
  gcp_iam_policy,
  jsonb_array_elements(bindings) as p,
  jsonb_array_elements_text(p -> 'members') as entity;