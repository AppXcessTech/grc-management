select
  name,
  address,
  id,
  jsonb_pretty(users)
from
  gcp_compute_address where name= 'test2';