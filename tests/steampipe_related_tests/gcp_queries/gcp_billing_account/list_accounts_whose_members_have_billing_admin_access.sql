select
  name,
  display_name,
  jsonb_array_elements_text(i -> 'members') as members,
  i ->> 'role' as role
from
  gcp_billing_account,
  jsonb_array_elements(iam_policy -> 'bindings') as i
where
  i ->> 'role' like '%billing.admin';