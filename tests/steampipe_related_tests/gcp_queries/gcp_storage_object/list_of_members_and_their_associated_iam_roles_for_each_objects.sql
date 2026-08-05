select
  bucket,
  name,
  p -> 'members' as member,
  p ->> 'role' as role,
  p ->> 'version' as version
from
  gcp_storage_object,
  jsonb_array_elements(iam_policy -> 'bindings') as p
where
  bucket = 'steampipe-test';