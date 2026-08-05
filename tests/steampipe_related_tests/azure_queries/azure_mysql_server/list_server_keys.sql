select
  name as server_name,
  id as server_id,
  keys ->> 'creationDate' as keys_creation_date,
  keys ->> 'id' as keys_id,
  keys ->> 'kind' as keys_kind,
  keys ->> 'name' as keys_name,
  keys ->> 'serverKeyType' as keys_server_key_type,
  keys ->> 'type' as keys_type,
  keys ->> 'uri' as keys_uri
from
  azure_mysql_server,
  jsonb_array_elements(server_keys) as keys;