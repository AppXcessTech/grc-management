select
  gateway.name as vpn_gateway_name,
  tunnel.peer_ip,
  tunnel.name as tunnel_name
from
  gcp_compute_target_vpn_gateway as gateway,
  jsonb_array_elements_text(tunnels) as t
  join gcp_compute_vpn_tunnel as tunnel
  on t = tunnel.self_link;