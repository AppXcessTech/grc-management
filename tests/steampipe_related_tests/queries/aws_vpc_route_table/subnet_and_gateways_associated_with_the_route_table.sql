select
  route_table_id,
  associations_detail -> 'AssociationState' ->> 'State' as state,
  associations_detail -> 'GatewayId' as gateway_id,
  associations_detail -> 'SubnetId' as subnet_id,
  associations_detail -> 'RouteTableAssociationId' as route_table_association_id,
  associations_detail -> 'Main' as main_route_table
from
  aws_vpc_route_table
  cross join jsonb_array_elements(associations) as associations_detail;