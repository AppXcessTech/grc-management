select
  name,
  location,
  p -> 'members' as member,
  p ->> 'role' as role
from
  gcp_storage_bucket,
  jsonb_array_elements(iam_policy -> 'bindings') as p;