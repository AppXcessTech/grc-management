select
  db_instance_identifier,
  class,
  allocated_storage,
  deletion_protection
from
  aws_rds_db_instance
where
  not storage_encrypted;