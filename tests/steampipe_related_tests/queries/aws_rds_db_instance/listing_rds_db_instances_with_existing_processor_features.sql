select
  db_instance_identifier,
  class,
  engine,
  engine_version,
  kms_key_id,
  processor_features
from
  aws_rds_db_instance
where
  processor_features is not null;