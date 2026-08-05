select
  name,
  scale_set_name,
  id,
  sku_name,
  sku_tier
from
  azure_compute_virtual_machine_scale_set_vm
where 
  scale_set_name = 'my_vm_scale';