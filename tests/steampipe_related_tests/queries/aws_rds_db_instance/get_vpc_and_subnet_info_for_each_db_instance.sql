select
  db_instance_identifier as attached_vpc,
  vsg ->> 'VpcSecurityGroupId' as vpc_security_group_id,
  vsg ->> 'Status' as status,
  sub -> 'SubnetAvailabilityZone' ->> 'Name' as subnet_availability_zone,
  sub ->> 'SubnetIdentifier' as subnet_identifier,
  sub -> 'SubnetOutpost' ->> 'Arn' as subnet_outpost,
  sub ->> 'SubnetStatus' as subnet_status
from
  aws_rds_db_instance
  cross join jsonb_array_elements(vpc_security_groups) as vsg
  cross join jsonb_array_elements(subnets) as sub;