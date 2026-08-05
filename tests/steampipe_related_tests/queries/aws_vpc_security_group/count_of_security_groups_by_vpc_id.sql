select
  vpc_id,
  count(vpc_id) as count
from
  aws_vpc_security_group
group by
  vpc_id;