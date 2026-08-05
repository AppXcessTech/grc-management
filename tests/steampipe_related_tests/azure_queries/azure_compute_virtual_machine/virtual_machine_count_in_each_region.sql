select
  region,
  count(name)
from
  azure_compute_virtual_machine
group by
  region;