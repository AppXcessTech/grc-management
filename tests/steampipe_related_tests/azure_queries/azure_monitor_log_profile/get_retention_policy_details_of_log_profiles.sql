select
  id,
  name,
  retention_policy -> 'Enabled' as retention_policy_enabled,
  retention_policy -> 'Days' as retention_policy_days
from
  azure_monitor_log_profile;