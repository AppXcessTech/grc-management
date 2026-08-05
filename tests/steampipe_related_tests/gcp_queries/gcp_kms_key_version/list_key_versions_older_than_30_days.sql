select
  key_name,
  create_time,
  crypto_key_version,
  state
from
  gcp_kms_key_version
where
  create_time <= (current_date - interval '30' day) and
  state <> 'DESTROYED'
order by
  create_time;