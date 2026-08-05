select
  name,
  jsonb_array_length(availability_zones) as az_count
from
  aws_ec2_autoscaling_group
where
  jsonb_array_length(availability_zones) < 2;