select
  vpc_id,
  count(subnet_id) as subnet_count
from
  aws_vpc_subnet
group by
  vpc_id;