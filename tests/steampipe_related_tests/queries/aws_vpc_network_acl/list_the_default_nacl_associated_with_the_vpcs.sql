select
  network_acl_id,
  vpc_id,
  is_default
from
  aws_vpc_network_acl
where
  is_default = true;