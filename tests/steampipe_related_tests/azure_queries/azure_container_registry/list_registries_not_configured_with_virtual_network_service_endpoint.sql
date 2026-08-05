select
  name,
  network_rule_set ->> 'defaultAction' as network_rule_default_action,
  network_rule_set ->> 'virtualNetworkRules' as virtual_network_rules
from
  azure_container_registry
where
  network_rule_set is not null
  and network_rule_set ->> 'defaultAction' = 'Allow';