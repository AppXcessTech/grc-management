select
  id,
  name,
  type,
  provisioning_state
from
  azure_mssql_virtual_machine
where
  provisioning_state = 'Failed';