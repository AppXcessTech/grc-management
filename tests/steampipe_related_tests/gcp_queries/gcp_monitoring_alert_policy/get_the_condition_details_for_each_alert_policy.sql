select
  display_name,
  con ->> 'displayName' as filter_display_name,
  con -> 'conditionThreshold' ->> 'filter' as filter,
  con -> 'conditionThreshold' ->> 'thresholdValue' as threshold_value,
  con -> 'conditionThreshold' ->> 'trigger' as trigger
from
  gcp_monitoring_alert_policy,
  jsonb_array_elements(conditions) as con;