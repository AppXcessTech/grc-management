select
  id,
  name,
  jsonb_pretty(web_application_firewall_configuration -> 'disabledRuleGroups') as disabled_rule_groups,
  web_application_firewall_configuration -> 'enabled' as enabled,
  jsonb_pretty(web_application_firewall_configuration -> 'exclusions') as exclusions,
  web_application_firewall_configuration -> 'fileUploadLimitInMb' as file_upload_limit_in_mb,
  web_application_firewall_configuration -> 'firewallMode' as firewall_mode,
  web_application_firewall_configuration -> 'maxRequestBodySizeInKb' as max_request_body_size_in_kb,
  web_application_firewall_configuration -> 'requestBodyCheck' as request_body_check,
  web_application_firewall_configuration -> 'ruleSetType' as rule_set_type,
  web_application_firewall_configuration -> 'ruleSetVersion' as rule_set_version
from
  azure_application_gateway;