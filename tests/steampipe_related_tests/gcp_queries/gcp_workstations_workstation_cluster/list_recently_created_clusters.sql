select
  name,
  display_name,
  create_time,
  location
from
  gcp_workstations_workstation_cluster
order by
  create_time desc
limit
  10;