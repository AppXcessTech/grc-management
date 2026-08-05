select
  id,
  enabled as key_enabled
from
  aws_kms_key
where
  not enabled;