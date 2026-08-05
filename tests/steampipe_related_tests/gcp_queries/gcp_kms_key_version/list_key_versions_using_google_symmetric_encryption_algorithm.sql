select
  key_name,
  create_time,
  crypto_key_version,
  algorithm
from
  gcp_kms_key_version
where
  algorithm like 'GOOGLE_SYMMETRIC_ENCRYPTION'
order by
  create_time;