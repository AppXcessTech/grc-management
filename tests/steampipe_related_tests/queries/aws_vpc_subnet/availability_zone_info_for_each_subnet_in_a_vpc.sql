select
  vpc_id,
  subnet_id,
  availability_zone,
  availability_zone_id
from
  aws_vpc_subnet
order by
  vpc_id,
  availability_zone;