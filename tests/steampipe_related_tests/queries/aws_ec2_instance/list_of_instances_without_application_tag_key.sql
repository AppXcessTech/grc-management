select
  instance_id,
  tags
from
  aws_ec2_instance
where
  not tags :: JSONB ? 'application';