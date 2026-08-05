select
  id,
  name,
  settings -> 'id' as settings_id,
  settings -> 'name' as settings_name,
  settings -> 'properties' -> 'cookieBasedAffinity' as settings_cookie_based_affinity,
  settings -> 'properties' -> 'pickHostNameFromBackendAddress' as settings_pick_host_name_from_backend_address,
  settings -> 'properties' -> 'port' as settings_port,
  settings -> 'properties' -> 'protocol' as settings_protocol,
  settings -> 'properties' -> 'requestTimeout' as settings_request_timeout
from
  azure_application_gateway,
  jsonb_array_elements(backend_http_settings_collection) as settings;