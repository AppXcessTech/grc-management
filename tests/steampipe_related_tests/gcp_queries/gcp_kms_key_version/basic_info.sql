select
  key_name,
  crypto_key_version,
  title,
  state
from
  gcp_kms_key_version
where
  state <> 'DESTROYED';