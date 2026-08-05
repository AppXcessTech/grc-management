select 
  i.instance_id, 
  i.vpc_id, 
  i.subnet_id, 
  s.tags ->> 'Name' as subnet_name
from 
  aws_ec2_instance as i, 
  aws_vpc_subnet as s 
where 
  i.subnet_id = s.subnet_id;