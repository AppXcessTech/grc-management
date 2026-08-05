select
  name,
  display_name,
  conditions,
  location
from
  gcp_workstations_workstation_cluster
where
  conditions is not null;