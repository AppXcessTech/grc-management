select
  name,
  display_name,
  jsonb_array_elements_text(p -> 'members') as member,
  p ->> 'role' as role
from
  gcp_billing_account,
  jsonb_array_elements(iam_policy -> 'bindings') as p;