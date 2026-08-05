select
  event_name,
  id,
  operation_name,
  event_timestamp,
  level,
  caller
from
  azure_monitor_log_profile
where
  level = 'EventLevelCritical';