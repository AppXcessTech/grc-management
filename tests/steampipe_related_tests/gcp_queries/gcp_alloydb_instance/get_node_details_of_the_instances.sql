select
  name,
  node -> 'Id' as node_id,
  node -> 'Ip' as node_ip,
  node -> 'State' as node_state,
  node -> 'ZoneId' as node_zone_id
from
  gcp_alloydb_instance,
  jsonb_array_elements(nodes) as node;