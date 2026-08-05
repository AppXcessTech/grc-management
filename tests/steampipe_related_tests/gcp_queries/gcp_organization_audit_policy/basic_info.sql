select
  organization_id,
  service,
  jsonb_array_elements(audit_log_configs) ->> 'logType' as log_type
from
  gcp_organization_audit_policy;