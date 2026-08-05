select
  name,
  bgp_asn,
  bgp_advertise_mode,
  bgp_advertised_ip_ranges
from
  gcp_compute_router
where bgp_advertise_mode = 'CUSTOM';