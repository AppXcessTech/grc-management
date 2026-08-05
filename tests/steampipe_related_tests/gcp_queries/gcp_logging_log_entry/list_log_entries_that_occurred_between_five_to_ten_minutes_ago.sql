select
  log_name,
  insert_id,
  receive_timestamp,
  trace_sampled,
  severity,
  resource_type
from
  gcp_logging_log_entry
where
  log_name = 'projects/parker-abbb/logs/cloudaudit.googleapis.com%2Factivity'
and
  timestamp between (now() - interval '10 minutes') and (now() - interval '5 minutes')
order by
  receive_timestamp asc;