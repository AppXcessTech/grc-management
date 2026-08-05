select
  id,
  name,
  type,
  provisioning_state
from
  azure_lb_backend_address_pool
where
  provisioning_state = 'Failed';