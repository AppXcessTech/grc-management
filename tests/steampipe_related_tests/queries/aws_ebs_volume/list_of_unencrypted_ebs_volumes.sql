select
  volume_id,
  encrypted
from
  aws_ebs_volume
where
  not encrypted;