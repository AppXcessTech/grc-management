select
  log_name,
  insert_id,
  receive_timestamp,
  trace_sampled,
  span_id,
  timestamp
from
  gcp_logging_log_entry
where
  timestamp >= now() - interval '30' day;