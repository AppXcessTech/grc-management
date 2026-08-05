select
  name,
  create_time,
  rotation_period
from
  gcp_kms_key
where
  split_part(rotation_period, 's', 1) :: int > 7776000;