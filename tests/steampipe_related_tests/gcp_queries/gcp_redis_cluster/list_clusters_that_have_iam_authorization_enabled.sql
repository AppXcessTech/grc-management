select
  name,
  create_time,
  location,
  psc_connections[0] ->> 'address' as address
from
  gcp_redis_cluster
where
  authorization_mode = 1;