select
  name,
  access_log_enabled
from
  aws_ec2_classic_load_balancer
where
  access_log_enabled = 'false';