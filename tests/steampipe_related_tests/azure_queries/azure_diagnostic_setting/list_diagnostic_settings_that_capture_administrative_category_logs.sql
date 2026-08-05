select
  name,
  id,
  type
from
  azure_diagnostic_setting,
  jsonb_array_elements(logs) as l
where
  l ->> 'category' = 'Administrative'
  and l ->> 'enabled' = 'true';