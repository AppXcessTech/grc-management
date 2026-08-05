select
  id,
  name,
  listeners -> 'id' as listener_id,
  listeners -> 'name' as listener_name,
  jsonb_pretty(listeners -> 'properties' -> 'frontendPort') as listener_frontend_port,
  jsonb_pretty(listeners -> 'properties' -> 'hostNames') as listener_host_names,
  listeners -> 'properties' -> 'protocol' as listener_protocol,
  listeners -> 'properties' -> 'requireServerNameIndication' as listener_require_server_name_indication
from
  azure_application_gateway,
  jsonb_array_elements(http_listeners) as listeners;