select
  name as workspace_name,
  id as workspace_id,
  connections ->> 'id' as connection_id,
  connections ->> 'privateEndpointPropertyId' as connection_private_endpoint_property_id,
  connections ->> 'privateLinkServiceConnectionStateActionsRequired' as connection_actions_required,
  connections ->> 'privateLinkServiceConnectionStateDescription' as connection_description,
  connections ->> 'privateLinkServiceConnectionStateStatus' as connection_status,
  connections ->> 'provisioningState' as connection_provisioning_state
from
  azure_synapse_workspace,
  jsonb_array_elements(private_endpoint_connections) as connections;