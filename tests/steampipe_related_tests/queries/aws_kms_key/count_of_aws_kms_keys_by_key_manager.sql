select
  key_manager,
  count(key_manager) as count
from
  aws_kms_key
group by
  key_manager;