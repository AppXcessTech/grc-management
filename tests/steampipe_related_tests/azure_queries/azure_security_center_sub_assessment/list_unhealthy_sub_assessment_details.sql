select
  name,
  type,
  category,
  status
from
  azure_security_center_sub_assessment
where
  status ->> 'Code' = 'Unhealthy';