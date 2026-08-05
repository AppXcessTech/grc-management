select
  vm.name,
  disk.encryption_type
from
  azure_compute_disk as disk
  join azure_compute_virtual_machine as vm on disk.name = vm.os_disk_name
where
  not disk.encryption_type = 'EncryptionAtRestWithCustomerKey';