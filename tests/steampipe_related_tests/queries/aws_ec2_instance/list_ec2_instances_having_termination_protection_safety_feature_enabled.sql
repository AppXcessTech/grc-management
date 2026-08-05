select
  instance_id,
  disable_api_termination
from
  aws_ec2_instance
where
  not disable_api_termination;