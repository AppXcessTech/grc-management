select
  name,
  scope,
  type,
  principal_id.
  principal_type
from
  azure_role_assignment
where
  scope = '/subscriptions/abcdef12-3456-7890-abcd-ef1234567890/resourceGroups/my-rg'