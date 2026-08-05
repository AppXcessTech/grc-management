select
  name,
  display_name,
  network,
  subnetwork,
  location
from
  gcp_workstations_workstation_cluster
where
  location = 'us-central1';