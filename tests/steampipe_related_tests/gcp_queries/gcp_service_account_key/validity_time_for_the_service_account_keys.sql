select
  title,
  service_account_name as service_account,
  valid_after_time,
  valid_before_time
from
  gcp_service_account_key;