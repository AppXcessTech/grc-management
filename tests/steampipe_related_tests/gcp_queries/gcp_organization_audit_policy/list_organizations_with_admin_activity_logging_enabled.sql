select
  organization_id,
  service,
  log_type ->> 'logType' as log_type
from
  gcp_organization_audit_policy,
  jsonb_array_elements(audit_log_configs) as log_type
where
  log_type ->> 'logType' = 'ADMIN_READ';