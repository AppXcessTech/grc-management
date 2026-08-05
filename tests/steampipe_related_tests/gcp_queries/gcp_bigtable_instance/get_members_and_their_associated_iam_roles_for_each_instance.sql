select
  name,
  location,
  jsonb_array_elements_text(p -> 'members') as member,
  p ->> 'role' as role
from
  gcp_bigtable_instance,
  jsonb_array_elements(iam_policy -> 'bindings') as p;