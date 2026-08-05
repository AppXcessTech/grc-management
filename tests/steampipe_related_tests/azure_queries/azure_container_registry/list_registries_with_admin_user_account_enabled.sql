select
  name,
  admin_user_enabled,
  region
from
  azure_container_registry
where
  admin_user_enabled;