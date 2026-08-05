select
  name,
  continuous_backups_status
from
  aws_dynamodb_table
where
  continuous_backups_status = 'DISABLED';