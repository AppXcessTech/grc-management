select
  db_cluster_identifier,
  status,
  cluster_create_time,
  kms_key_id,
  storage_encrypted
from
  aws_docdb_cluster
where
  not storage_encrypted;