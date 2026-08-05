select
  name,
  display_name,
  type,
  verification_status
from
  gcp_monitoring_notification_channel
where
  verification_status <> 'VERIFIED';