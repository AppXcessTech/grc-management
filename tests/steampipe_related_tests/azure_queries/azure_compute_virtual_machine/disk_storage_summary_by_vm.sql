select
  vm.name,
  count(d) as num_disks,
  sum(d.disk_size_gb) as total_disk_size_gb
from
  azure.azure_compute_virtual_machine as vm
  left join azure_compute_disk as d on lower(vm.id) = lower(d.managed_by)
group by
  vm.name
order by
  vm.name;