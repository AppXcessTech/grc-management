select
  g.name as instance_group_name,
  n.name as network_name,
  s.name as subnetwork_name,
  s.ip_cidr_range,
  s.gateway_address,
  n.location
from
  gcp_compute_instance_group as g,
  gcp_compute_network as n,
  gcp_compute_subnetwork as s
where
  g.network = n.self_link
  and g.subnetwork = s.self_link;