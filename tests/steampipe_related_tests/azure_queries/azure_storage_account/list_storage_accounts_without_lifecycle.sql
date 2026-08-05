select
  name,
  lifecycle_management_policy -> 'properties' -> 'policy' -> 'rules' as lifecycle_rules
from
  azure_storage_account
where
  lifecycle_management_policy -> 'properties' -> 'policy' -> 'rules' is null;