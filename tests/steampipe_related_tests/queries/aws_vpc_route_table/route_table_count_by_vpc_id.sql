select
  vpc_id,
  count(route_table_id) as route_table_count
from
  aws_vpc_route_table
group by
  vpc_id;