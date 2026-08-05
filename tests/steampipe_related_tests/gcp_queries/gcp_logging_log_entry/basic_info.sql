select
  log_name,
  insert_id,
  log_entry_operation_first,
  log_entry_operation_id,
  receive_timestamp
from
  gcp_logging_log_entry;