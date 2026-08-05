select
  subnet_id,
  cidr_block,
  available_ip_address_count,
  power(2, 32 - masklen(cidr_block :: cidr)) -1 as raw_size
from
  aws_vpc_subnet;