select
  name,
  display_name,
  create_time,
  location_id,
  memory_size_gb,
  reserved_ip_range
from
  gcp_redis_instance
where
  create_time >= current_timestamp - interval '7 days';