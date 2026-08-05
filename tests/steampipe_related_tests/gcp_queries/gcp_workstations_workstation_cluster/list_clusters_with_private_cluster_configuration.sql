select
  name,
  display_name,
  private_cluster_config,
  network,
  subnetwork,
  location
from
  gcp_workstations_workstation_cluster
where
  private_cluster_config is not null;