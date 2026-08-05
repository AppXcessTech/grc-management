select
  name,
  id,
  type
from
  azure_log_alert,
  jsonb_array_elements(condition -> 'allOf') as l
where
  l ->> 'equals' = 'Microsoft.Authorization/policyAssignments/write';