select
  volume_id,
  size,
  att ->> 'InstanceId' as instance_id
from
  aws_ebs_volume
  cross join jsonb_array_elements(attachments) as att
  join aws_ec2_instance as i on i.instance_id = att ->> 'InstanceId'
where
  instance_state = 'stopped';