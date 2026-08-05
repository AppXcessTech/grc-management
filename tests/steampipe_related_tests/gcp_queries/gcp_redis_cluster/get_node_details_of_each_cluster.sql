select
  name,
  create_time,
  location,
  node_type,
  size_gb,
  replica_count,
  shard_count
from
  gcp_redis_cluster
where
  name = 'cluster-test'
  and location = 'europe-west9';