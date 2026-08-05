select
  f.name as function_name,
  f.service_account_email as service_account_email,
  a.display_name as service_account_display_name,
  b ->> 'role' as role_name
from
  gcp_cloudfunctions_function as f,
  gcp_service_account as a,
  gcp_iam_policy as p,
  jsonb_array_elements(bindings) as b,
  jsonb_array_elements_text(b -> 'members') as m
where
  f.service_account_email = a.email
  and m = ( 'serviceAccount:' || f.service_account_email);