select
  name,
  jsonb_array_elements_text(security_groups) as attached_security_group
from
  aws_ec2_application_load_balancer;