select
  file_system_id,
  encrypted,
  kms_key_id,
  region
from
  aws_efs_file_system
where
  not encrypted;