select
  instance_id,
  sg ->> 'GroupId' as group_id,
  sg ->> 'GroupName' as group_name
from
  aws_ec2_instance
  cross join jsonb_array_elements(security_groups) as sg
where
  sg ->> 'GroupName' = 'default';