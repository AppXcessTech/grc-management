select
  placement_availability_zone as az,
  instance_type,
  count(*)
from
  aws_ec2_instance
group by
  placement_availability_zone,
  instance_type;