select
  name,
  id,
  rule ->> 'Name' as rule_name,
  rule ->> 'Type' as rule_type,
  rule -> 'FirewallRuleProperties' ->> 'endIpAddress' as end_ip_address,
  rule -> 'FirewallRuleProperties' ->> 'startIpAddress' as start_ip_address
from
  azure_postgresql_server,
  jsonb_array_elements(firewall_rules) as rule
where
  rule ->> 'Name' = 'AllowAllWindowsAzureIps'
  and rule -> 'FirewallRuleProperties' ->> 'startIpAddress' = '0.0.0.0'
  and rule -> 'FirewallRuleProperties' ->> 'endIpAddress' = '0.0.0.0';