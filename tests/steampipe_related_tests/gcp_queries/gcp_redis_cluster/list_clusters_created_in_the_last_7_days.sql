select
  name,
  create_time,
  location,
  psc_connections[0] ->> 'address' as address
from
  gcp_redis_cluster
where
  create_time >= current_timestamp - interval '7 days';