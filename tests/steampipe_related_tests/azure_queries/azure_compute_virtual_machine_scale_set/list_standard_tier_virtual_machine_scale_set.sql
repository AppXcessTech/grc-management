select
  name,
  id,
  sku_name,
  sku_tier
from
  azure_compute_virtual_machine_scale_set
where
  sku_tier = 'Standard';