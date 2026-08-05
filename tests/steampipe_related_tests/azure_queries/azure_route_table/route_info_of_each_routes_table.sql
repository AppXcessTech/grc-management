select
  name,
  route ->> 'name' route_name,
  route -> 'properties' ->> 'addressPrefix' address_prefix,
  route -> 'properties' ->> 'nextHopType' next_hop_type
from
  azure_route_table
  cross join jsonb_array_elements(routes) as route;