select
  name,
  create_time,
  location,
  size_gb,
  precise_size_gb,
  psc_connections[0] ->> 'address' as address
from
  gcp_redis_cluster;