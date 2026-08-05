select
  id,
  name,
  type,
  provisioning_state,
  public_network_access
from
  azure_synapse_workspace
where
  public_network_access = 'Enabled';