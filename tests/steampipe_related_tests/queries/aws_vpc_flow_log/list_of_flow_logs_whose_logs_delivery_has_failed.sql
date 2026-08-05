select
  flow_log_id,
  resource_id,
  deliver_logs_error_message,
  deliver_logs_status
from
  aws_vpc_flow_log
where
  deliver_logs_status = 'FAILED';