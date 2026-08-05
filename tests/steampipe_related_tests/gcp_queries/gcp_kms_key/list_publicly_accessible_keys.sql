select
  distinct name,
  key_ring_name,
  location
from
  gcp_kms_key,
  jsonb_array_elements(iam_policy -> 'bindings') as b
where
  b -> 'members' ?| array['allAuthenticatedUsers', 'allUsers'];