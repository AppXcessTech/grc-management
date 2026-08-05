select
  service_account_name as service_account,
  title,
  key_type
from
  gcp_service_account_key
where
  key_type = 'USER_MANAGED';