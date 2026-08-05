select
  n.name,
  n.id,
  n.creation_timestamp,
  n.mtu,
  n.routing_mode,
  n.location,
  n.project
from
  gcp_compute_ha_vpn_gateway g,
  gcp_compute_network n
where
  g.network = n.self_link;