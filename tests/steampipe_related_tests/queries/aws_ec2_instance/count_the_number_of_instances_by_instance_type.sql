select
  instance_type,
  count(instance_type) as count
from
  aws_ec2_instance
group by
  instance_type;