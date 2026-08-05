select
  log_name,
  insert_id,
  resource_type,
  severity,
  span_id,
  timestamp
from
  gcp_logging_log_entry
where
  severity = 'NOTICE';