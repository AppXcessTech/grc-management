select
  name,
  b ->> 'role' as role_name,
  m as member
from
  gcp_cloudfunctions_function,
  jsonb_array_elements(iam_policy -> 'bindings') as b,
  jsonb_array_elements_text(b -> 'members') as m
where
  m not like '%@turbot.com';