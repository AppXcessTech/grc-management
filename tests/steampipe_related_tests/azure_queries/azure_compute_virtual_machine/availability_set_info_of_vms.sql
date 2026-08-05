select
  vm.name vm_name,
  aset.name availability_set_name,
  aset.platform_fault_domain_count,
  aset.platform_update_domain_count,
  aset.sku_name
from
  azure_compute_availability_set as aset
  join azure_compute_virtual_machine as vm on lower(aset.id) = lower(vm.availability_set_id);