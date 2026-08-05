select
  log_name,
  insert_id,
  receive_timestamp,
  resource_type,
  severity
from
  gcp_logging_log_entry
where
  filter = 'resource.type = "gce_instance" and (severity = ERROR OR "error")';