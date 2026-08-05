select
  volume_type,
  count(volume_type) as count
from
  aws_ebs_volume
group by
  volume_type;