select
  id,
  key_state,
  deletion_date
from
  aws_kms_key
where
  key_state = 'PendingDeletion';