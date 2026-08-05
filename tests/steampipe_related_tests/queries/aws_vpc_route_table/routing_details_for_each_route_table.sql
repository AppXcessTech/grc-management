select
  route_table_id,
  route_detail -> 'CarrierGatewayId' ->> 'State' as carrier_gateway_id,
  route_detail -> 'DestinationCidrBlock' as destination_CIDR_block,
  route_detail -> 'DestinationIpv6CidrBlock' as destination_ipv6_CIDR_block,
  route_detail -> 'EgressOnlyInternetGatewayId' as egress_only_internet_gateway,
  route_detail -> 'GatewayId' as gateway_id,
  route_detail -> 'InstanceId' as instance_id,
  route_detail -> 'InstanceOwnerId' as instance_owner_id,
  route_detail -> 'LocalGatewayId' as local_gateway_id,
  route_detail -> 'NatGatewayId' as nat_gateway_id,
  route_detail -> 'NetworkInterfaceId' as network_interface_id,
  route_detail -> 'TransitGatewayId' as transit_gateway_id,
  route_detail -> 'VpcPeeringConnectionId' as vpc_peering_connection_id
from
  aws_vpc_route_table
  cross join jsonb_array_elements(routes) as route_detail;