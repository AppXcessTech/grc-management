select
  name,
  tags
from
  azure_application_security_group
where
  not tags :: JSONB ? 'owner';