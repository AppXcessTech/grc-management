select
  display_name,
  name,
  enabled,
  documentation ->> 'content' as doc_content,
  tags
from
  gcp_monitoring_alert_policy;