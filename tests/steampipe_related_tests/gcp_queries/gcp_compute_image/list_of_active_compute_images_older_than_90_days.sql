select
  name,
  creation_timestamp,
  age(creation_timestamp),
  deprecation_state
from
  gcp_compute_image
where
  creation_timestamp <= (current_date - interval '90' day)
  and deprecation_state = 'ACTIVE'
order by
  creation_timestamp;