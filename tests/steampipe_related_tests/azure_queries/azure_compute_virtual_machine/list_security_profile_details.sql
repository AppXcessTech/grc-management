select
  name,
  vm_id,
  security_profile -> 'encryptionAtHost' as encryption_at_host
from
  azure_compute_virtual_machine;