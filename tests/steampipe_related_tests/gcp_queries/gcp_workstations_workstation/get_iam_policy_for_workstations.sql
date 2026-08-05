select
  name,
  i -> 'condition' as condition,
  i -> 'members' as members,
  i ->> 'role' as role
from
  gcp_workstations_workstation,
  jsonb_array_elements(iam_policy -> 'bindings') as i;