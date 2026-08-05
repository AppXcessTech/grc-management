select
  name,
  subnet ->> 'name' as subnet_name,
  subnet -> 'properties' ->> 'addressPrefix' as address_prefix,
  subnet -> 'properties' ->> 'privateEndpointNetworkPolicies' as private_endpoint_network_policies,
  subnet -> 'properties' ->> 'privateLinkServiceNetworkPolicies' as private_link_service_network_policies,
  subnet -> 'properties' ->> 'serviceEndpoints' as service_endpoints,
  split_part(subnet -> 'properties' ->> 'routeTable', '/', 9) as route_table
from
  azure_virtual_network
  cross join jsonb_array_elements(subnets) as subnet;