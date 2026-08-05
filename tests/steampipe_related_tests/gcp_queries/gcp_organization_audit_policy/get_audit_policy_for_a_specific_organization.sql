select
  organization_id,
  service,
  audit_log_configs
from
  gcp_organization_audit_policy
where
  organization_id = '123456789';