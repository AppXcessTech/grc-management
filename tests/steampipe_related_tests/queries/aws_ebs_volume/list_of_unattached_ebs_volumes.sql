select
  volume_id,
  volume_type
from
  aws_ebs_volume
where
  jsonb_array_length(attachments) = 0;