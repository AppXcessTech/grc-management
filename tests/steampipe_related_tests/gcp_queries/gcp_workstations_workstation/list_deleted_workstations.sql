select
  name,
  display_name,
  state,
  delete_time,
  location
from
  gcp_workstations_workstation
where
  delete_time is not null;