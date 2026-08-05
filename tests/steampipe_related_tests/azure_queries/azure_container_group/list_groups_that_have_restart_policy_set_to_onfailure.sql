select
  name,
  restart_policy,
  provisioning_state,
  type
from
  azure_container_group
where
  restart_policy = "OnFailure";