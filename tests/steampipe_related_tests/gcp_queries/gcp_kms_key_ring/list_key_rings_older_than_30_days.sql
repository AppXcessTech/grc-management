select
  name,
  create_time
from
  gcp_kms_key_ring
where
  create_time <= (current_date - interval '30' day)
order by
  create_time;