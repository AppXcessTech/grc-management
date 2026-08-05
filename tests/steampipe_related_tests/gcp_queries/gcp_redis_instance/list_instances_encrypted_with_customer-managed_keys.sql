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
  customer_managed_key is not null;