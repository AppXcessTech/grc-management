select
  st.name subnet_name,
  st.virtual_network_name,
  rt.name route_table_name,
  jsonb_array_elements(rt.routes) -> 'properties' ->> 'addressPrefix' as route_address_prefix,
  jsonb_array_elements(rt.routes) -> 'properties' ->> 'nextHopType' as route_next_hop_type
from
  azure_route_table as rt
  join azure_subnet st on rt.id = st.route_table_id;