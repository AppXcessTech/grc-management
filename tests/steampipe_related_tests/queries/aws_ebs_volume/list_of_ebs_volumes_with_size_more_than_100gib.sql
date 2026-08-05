select
  volume_id,
  size
from
  aws_ebs_volume
where
  size > '100';