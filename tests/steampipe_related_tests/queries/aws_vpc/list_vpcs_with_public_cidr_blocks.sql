select
  vpc_id,
  cidr_block,
  state,
  region
from
  aws_vpc
where
  not cidr_block <<= '10.0.0.0/8'
  and not cidr_block <<= '192.168.0.0/16'
  and not cidr_block <<= '172.16.0.0/12';