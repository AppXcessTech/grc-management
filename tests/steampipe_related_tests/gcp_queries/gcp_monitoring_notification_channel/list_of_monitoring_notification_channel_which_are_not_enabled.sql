select
  name,
  display_name,
  enabled
from
  gcp_monitoring_notification_channel
where
  not enabled;