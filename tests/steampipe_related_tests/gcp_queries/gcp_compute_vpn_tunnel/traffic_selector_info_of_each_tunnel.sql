select
  name,
  jsonb_array_elements_text(local_traffic_selector) as local_traffic_selector,
  jsonb_array_elements_text(remote_traffic_selector) as remote_traffic_selector
from
  gcp_compute_vpn_tunnel;