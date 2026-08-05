select
  name,
  disable_bgp_route_propagation,
  region
from
  azure_route_table
where
  not disable_bgp_route_propagation;