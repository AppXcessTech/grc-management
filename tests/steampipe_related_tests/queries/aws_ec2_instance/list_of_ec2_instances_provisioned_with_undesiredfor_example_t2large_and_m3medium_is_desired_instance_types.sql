select
  instance_type,
  count(*) as count
from
  aws_ec2_instance
where
  instance_type not in ('t2.large', 'm3.medium')
group by
  instance_type;