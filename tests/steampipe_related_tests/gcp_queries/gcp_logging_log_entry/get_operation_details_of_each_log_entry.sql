select
  log_name,
  insert_id,
  operation_id,
  operation ->> 'Producer' as operation_producer,
  operation ->> 'First' as operation_first,
  operation ->> 'Last' as operation_last
from
  gcp_logging_log_entry;