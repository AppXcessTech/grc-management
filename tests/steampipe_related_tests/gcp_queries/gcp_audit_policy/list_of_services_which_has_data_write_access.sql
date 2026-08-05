select
  service,
  log_type ->> 'logType' as log_type
from
  gcp_audit_policy,
  jsonb_array_elements(audit_log_configs) as log_type
where
  log_type ->> 'logType' = 'DATA_WRITE';