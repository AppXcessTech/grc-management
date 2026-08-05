select
  id,
  key_rotation_enabled
from
  aws_kms_key
where
  not key_rotation_enabled;