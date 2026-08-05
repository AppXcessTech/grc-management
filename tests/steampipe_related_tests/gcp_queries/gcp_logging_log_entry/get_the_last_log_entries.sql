select
  log_name,
  insert_id,
  operation ->> 'Last' as log_entry_operation_last,
  receive_timestamp,
  resource_type,
  severity,
  text_payload
from
  gcp_logging_log_entry
where
  (operation ->> 'Last')::boolean;