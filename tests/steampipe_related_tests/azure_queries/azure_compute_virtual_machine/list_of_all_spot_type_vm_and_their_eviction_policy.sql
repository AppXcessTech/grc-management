select
  name,
  vm_id,
  eviction_policy
from
  azure_compute_virtual_machine
where
  priority = 'Spot';