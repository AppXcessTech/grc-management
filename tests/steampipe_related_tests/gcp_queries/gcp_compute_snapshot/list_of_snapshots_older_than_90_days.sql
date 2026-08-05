select
  name,
  creation_timestamp,
  age(creation_timestamp)
from
  gcp_compute_snapshot
where
  creation_timestamp <= (current_date - interval '90' day)
order by
  creation_timestamp;