select
  name,
  automatic_backups,
  arn,
  file_system_id
from
  aws_efs_file_system
where
  automatic_backups = 'enabled';