select
  size,
  count(*) as count
from
  azure_compute_virtual_machine
where
  size not in ('Standard_D8s_v3', 'Standard_DS3_v3')
group by
  size;