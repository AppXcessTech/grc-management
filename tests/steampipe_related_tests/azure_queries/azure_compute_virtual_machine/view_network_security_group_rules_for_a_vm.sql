select
  vm.name,
  nsg.name,
  jsonb_pretty(security_rules)
from
  azure.azure_compute_virtual_machine as vm,
  jsonb_array_elements(vm.network_interfaces) as vm_nic,
  azure_network_security_group as nsg,
  jsonb_array_elements(nsg.network_interfaces) as nsg_int
where
  lower(vm_nic ->> 'id') = lower(nsg_int ->> 'id')
  and vm.name = 'warehouse-01';