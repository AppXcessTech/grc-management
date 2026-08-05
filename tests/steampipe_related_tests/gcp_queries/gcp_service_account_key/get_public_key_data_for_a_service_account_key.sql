select
  name,
  key_type,
  key_origin,
  public_key_data_raw,
  public_key_data_pem
from
  gcp_service_account_key
where
  service_account_name = 'test@myproject.iam.gserviceaccount.com';