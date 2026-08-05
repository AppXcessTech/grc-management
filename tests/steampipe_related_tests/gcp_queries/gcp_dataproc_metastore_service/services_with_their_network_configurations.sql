select
  m.name as service_name,
  m.location,
  m.network,
  m.network_config,
  n.name as network_name,
  n.auto_create_subnetworks,
  n.peerings
from
  gcp_dataproc_metastore_service m
join
  gcp_compute_network n on n.name = split_part(m.network, '/', 5);