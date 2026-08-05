select
  name,
  table_properties -> 'Cors' as table_logging_cors,
  table_properties -> 'Logging' -> 'Read' as table_logging_read,
  table_properties -> 'Logging' -> 'Write' as table_logging_write,
  table_properties -> 'Logging' -> 'Delete' as table_logging_delete,
  table_properties -> 'Logging' ->> 'Version' as table_logging_version,
  table_properties -> 'Logging' -> 'RetentionPolicy' as table_logging_retention_policy,
  table_properties -> 'HourMetrics' -> 'Enabled' as table_hour_metrics_enabled,
  table_properties -> 'HourMetrics' -> 'IncludeAPIs' as table_hour_metrics_include_ap_is,
  table_properties -> 'HourMetrics' ->> 'Version' as table_hour_metrics_version,
  table_properties -> 'HourMetrics' -> 'RetentionPolicy' as table_hour_metrics_retention_policy,
  table_properties -> 'MinuteMetrics' -> 'Enabled' as table_minute_metrics_enabled,
  table_properties -> 'MinuteMetrics' -> 'IncludeAPIs' as table_minute_metrics_include_ap_is,
  table_properties -> 'MinuteMetrics' ->> 'Version' as table_minute_metrics_version,
  table_properties -> 'MinuteMetrics' -> 'RetentionPolicy' as table_minute_metrics_retention_policy
from
  azure_storage_account;