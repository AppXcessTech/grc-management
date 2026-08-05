select
  name,
  id,
  policy -> 'creationTime' as policy_creation_time,
  jsonb_pretty(policy -> 'disabledAlerts') as policy_disabled_alerts,
  policy -> 'emailAccountAdmins' as policy_email_account_admins,
  jsonb_pretty(policy -> 'emailAddresses') as policy_email_addresses,
  policy ->> 'id' as policy_id,
  policy ->> 'name' as policy_name,
  policy -> 'retentionDays' as policy_retention_days,
  policy ->> 'state' as policy_state,
  policy ->> 'storageAccountAccessKey' as policy_storage_account_access_key,
  policy ->> 'storageEndpoint' as policy_storage_endpoint,
  policy ->> 'type' as policy_type
from
  azure_mssql_managed_instance,
  jsonb_array_elements(security_alert_policies) as policy;