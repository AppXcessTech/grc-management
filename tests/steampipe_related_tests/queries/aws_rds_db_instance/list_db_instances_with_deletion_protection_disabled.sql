select
  db_instance_identifier,
  class,
  engine,
  engine_version,
  deletion_protection
from
  aws_rds_db_instance
where
  not deletion_protection;