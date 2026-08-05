select
  name,
  i -> 'Condition' as condition,
  i -> 'Members' as members,
  i ->> 'Role' as role
from
  gcp_cloud_run_job,
  jsonb_array_elements(iam_policy -> 'Bindings') as i;