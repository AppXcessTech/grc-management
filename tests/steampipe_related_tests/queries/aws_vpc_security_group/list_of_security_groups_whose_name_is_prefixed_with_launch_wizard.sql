select
  group_name,
  group_id
from
  aws_vpc_security_group
where
  group_name like '%launch-wizard%';