select
  name,
  display_name,
  jsonb_pretty(env) as environment_variables
from
  gcp_workstations_workstation;