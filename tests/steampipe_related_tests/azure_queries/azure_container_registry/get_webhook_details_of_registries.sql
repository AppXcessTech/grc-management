select
  name,
  w ->> 'location' as webhook_location,
  w -> 'properties' -> 'actions' as actions,
  w -> 'properties' ->> 'scope' as scope,
  w -> 'properties' ->> 'status' as status
from
  azure_container_registry,
  jsonb_array_elements(webhooks) as w;