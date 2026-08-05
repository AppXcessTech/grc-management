select
  key_name,
  max(crypto_key_version) crypto_key_version,
  state
from
  gcp_kms_key_version
where
  state like 'DISABLED'
group by
  key_name,
  state;