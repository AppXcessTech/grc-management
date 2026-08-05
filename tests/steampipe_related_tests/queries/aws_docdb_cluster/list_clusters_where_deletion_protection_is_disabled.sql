select
  db_cluster_identifier,
  status,
  cluster_create_time,
  deletion_protection
from
  aws_docdb_cluster
where
  not deletion_protection;