select
  log_name,
  insert_id,
  log_entry_operation_first,
  log_entry_operation_last,
  resource_type,
  span_id,
  text_payload
from
  gcp_logging_log_entry
where
  resource_type = 'audited_resource';