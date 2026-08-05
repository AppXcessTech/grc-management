select
  log_name,
  insert_id,
  split ->> 'Index' as split_index,
  split ->> 'TotalSplits' as total_splits,
  split ->> 'Uid' as split_uid
from
  gcp_logging_log_entry;