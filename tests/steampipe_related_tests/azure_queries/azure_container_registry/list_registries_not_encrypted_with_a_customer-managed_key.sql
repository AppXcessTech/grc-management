select
  name,
  encryption ->> 'status' as encryption_status,
  region
from
  azure_container_registry;