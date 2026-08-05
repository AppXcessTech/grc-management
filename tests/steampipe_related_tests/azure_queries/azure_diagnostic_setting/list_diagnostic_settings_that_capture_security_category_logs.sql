select
  name,
  id,
  type
from
  azure_diagnostic_setting,
  jsonb_array_elements(logs) as l
where
  l ->> 'category' = 'Security'
  and l ->> 'enabled' = 'true';