select
  name,
  i ->> 'Server' as server,
  i ->> 'Username' as username,
  i ->> 'Password' as password,
  i ->> 'Identity' as identity,
  i ->> 'IdentityURL' as identity_url
from
  azure_container_group,
  jsonb_array_elements(image_registry_credentials) as i;