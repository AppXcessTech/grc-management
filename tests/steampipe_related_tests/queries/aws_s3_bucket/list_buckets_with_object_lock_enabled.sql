select
  name,
  object_lock_configuration ->> 'ObjectLockEnabled' as object_lock_enabled
from
  aws_s3_bucket
where
  object_lock_configuration ->> 'ObjectLockEnabled' = 'Enabled';