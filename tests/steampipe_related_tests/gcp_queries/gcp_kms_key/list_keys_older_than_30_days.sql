select
  name,
  create_time,
  rotation_period
from
  gcp_kms_key
where
  create_time <= (current_date - interval '30' day)
order by
  create_time;