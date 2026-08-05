select
  name,
  lb ->> 'Key' as cross_zone,
  lb ->> 'Value' as cross_zone_value
from
  aws_ec2_network_load_balancer
  cross join jsonb_array_elements(load_balancer_attributes) as lb
where
  lb ->> 'Key' = 'load_balancing.cross_zone.enabled'
  and lb ->> 'Value' = 'false';