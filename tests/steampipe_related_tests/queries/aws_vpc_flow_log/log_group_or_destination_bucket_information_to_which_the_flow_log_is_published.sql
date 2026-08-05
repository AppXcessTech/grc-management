select
  flow_log_id,
  log_destination_type,
  log_destination,
  log_group_name,
  bucket_name
from
  aws_vpc_flow_log;