select
  name,
  instance_type,
  jsonb_array_elements_text(i -> 'members') as members,
  i ->> 'role' as role
from
  gcp_bigtable_instance,
  jsonb_array_elements(iam_policy -> 'bindings') as i
where
  i ->> 'role' like '%bigtable.admin';