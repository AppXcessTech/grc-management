select
  name,
  status,
  last_stop_timestamp
from
  gcp_compute_instance
where
  status = 'TERMINATED'
  and last_stop_timestamp < current_timestamp - interval '30 days' ;