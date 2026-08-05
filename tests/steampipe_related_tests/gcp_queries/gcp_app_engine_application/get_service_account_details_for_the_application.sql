select
  a.name,
  a.service_account,
  s.email,
  s.disabled,
  s.oauth2_client_id,
  s.iam_policy
from
  gcp_app_engine_application as a,
  gcp_service_account as s
where
  s.name = a.service_account;