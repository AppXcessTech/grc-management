select
  name,
  display_name,
  state,
  host,
  start_time,
  location
from
  gcp_workstations_workstation
where
  state = 'STATE_RUNNING';