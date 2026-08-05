select
  name,
  lb ->> 'Key' as logging_key,
  lb ->> 'Value' as logging_value
from
  aws_ec2_network_load_balancer
  cross join jsonb_array_elements(load_balancer_attributes) as lb
where
  lb ->> 'Key' = 'access_logs.s3.enabled'
  and lb ->> 'Value' = 'false';