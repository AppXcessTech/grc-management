select
  associations_detail ->> 'SubnetId' as subnet_id,
  route_table_id
from
  aws_vpc_route_table as rt
  cross join jsonb_array_elements(associations) as associations_detail
  join aws_vpc_subnet as sub on sub.subnet_id = associations_detail ->> 'SubnetId';