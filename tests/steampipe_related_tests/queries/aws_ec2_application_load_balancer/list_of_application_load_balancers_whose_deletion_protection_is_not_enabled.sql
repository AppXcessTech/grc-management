select
  name,
  lb ->> 'Key' as deletion_protection_key,
  lb ->> 'Value' as deletion_protection_value
from
  aws_ec2_application_load_balancer
  cross join jsonb_array_elements(load_balancer_attributes) as lb
where
  lb ->> 'Key' = 'deletion_protection.enabled'
  and lb ->> 'Value' = 'false';