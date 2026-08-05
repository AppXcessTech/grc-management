select
  db_cluster_identifier,
  backup_retention_period
from
  aws_docdb_cluster
where
  backup_retention_period > 7;