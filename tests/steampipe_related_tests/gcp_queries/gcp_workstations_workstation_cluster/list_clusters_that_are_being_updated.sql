select
  name,
  display_name,
  reconciling,
  update_time,
  location
from
  gcp_workstations_workstation_cluster
where
  reconciling = true;