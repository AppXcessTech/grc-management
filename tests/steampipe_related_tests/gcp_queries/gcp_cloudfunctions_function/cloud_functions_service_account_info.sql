select
  f.name as function_name,
  f.service_account_email as service_account_email,
  a.display_name as service_account_display_name
from
  gcp_cloudfunctions_function as f,
  gcp_service_account as a
where
  f.service_account_email = a.email;