select
  db_instance_identifier,
  iam_database_authentication_enabled
from
  aws_rds_db_instance
where
  not iam_database_authentication_enabled;