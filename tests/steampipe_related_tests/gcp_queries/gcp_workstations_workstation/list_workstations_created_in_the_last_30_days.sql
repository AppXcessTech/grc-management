select
  name,
  display_name,
  state,
  create_time,
  location
from
  gcp_workstations_workstation
where
  create_time >= now() - interval '30' day;