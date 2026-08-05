select
  c ->> 'PrivateEndpointConnectionName' as private_endpoint_connection_name,
  c ->> 'PrivateEndpointConnectionType' as private_endpoint_connection_type,
  c ->> 'PrivateEndpointId' as private_endpoint_id,
  c ->> 'PrivateLinkServiceConnectionStateActionsRequired' as private_link_service_connection_state_actions_required,
  c ->> 'PrivateLinkServiceConnectionStateDescription' as private_link_service_connection_state_description,
  c ->> 'PrivateLinkServiceConnectionStateStatus' as private_link_service_connection_state_status,
  c ->> 'ProvisioningState' as provisioning_state,
  c ->> 'PrivateEndpointConnectionId' as private_endpoint_connection_id
from
  azure_cosmosdb_account,
  jsonb_array_elements(private_endpoint_connections) as c;