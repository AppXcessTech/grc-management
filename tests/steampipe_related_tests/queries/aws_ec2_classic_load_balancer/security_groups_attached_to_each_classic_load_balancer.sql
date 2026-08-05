select
  name,
  jsonb_array_elements_text(security_groups) as sg
from
  aws_ec2_classic_load_balancer;