select
  id,
  name,
  type,
  provisioning_state
from
  azure_lb_rule
where
  provisioning_state = 'Failed';