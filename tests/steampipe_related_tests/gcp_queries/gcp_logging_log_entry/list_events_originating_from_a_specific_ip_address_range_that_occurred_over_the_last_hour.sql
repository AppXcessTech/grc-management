select
  log_name,
  insert_id,
  receive_timestamp,
  resource_type,
  severity,
  timestamp
from
  gcp_logging_log_entry
where
  filter = 'logName = "projects/my_project/logs/my_log" AND ip_in_net(jsonPayload.realClientIP, "10.1.2.0/24")'
  and timestamp >= now() - interval '1 hour'
order by
  receive_timestamp asc;