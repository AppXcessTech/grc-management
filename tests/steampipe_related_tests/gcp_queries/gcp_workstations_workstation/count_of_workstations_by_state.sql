select
  state,
  count(*)
from
  gcp_workstations_workstation
group by
  state;