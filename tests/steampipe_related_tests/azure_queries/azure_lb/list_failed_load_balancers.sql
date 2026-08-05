select
  id,
  name,
  type,
  provisioning_state
from
  azure_lb
where
  provisioning_state = 'Failed';