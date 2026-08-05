select
  volume_id,
  volume_type
from
  aws_ebs_volume
where
  volume_type = 'io1';