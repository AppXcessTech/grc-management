select
  name,
  id,
  jsonb_array_elements_text(p -> 'members') as members,
  p ->> 'role' as role
from
  gcp_compute_subnetwork,
  jsonb_array_elements(iam_policy -> 'bindings') as p
where
  p ->> 'role' = 'roles/compute.admin';