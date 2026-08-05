select
  name,
  display_name,
  create_time,
  location_id,
  jsonb_pretty(nodes) as instance_nodes
from
  gcp_redis_instance
where
  name = 'instance-test'
  and location_id = 'europe-west3-c';