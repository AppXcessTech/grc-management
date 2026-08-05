select
  db_instance_identifier,
  publicly_accessible
from
  aws_rds_db_instance
where
  publicly_accessible;