select
  name,
  scope,
  type,
  principal_id.
  principal_type
from
  azure_role_assignment
where
  scope = '/providers/Microsoft.Management/managementGroups/12345678-90ab-cdef-1234-567890abcdef'