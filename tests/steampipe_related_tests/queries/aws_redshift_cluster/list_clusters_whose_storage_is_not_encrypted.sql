select
  cluster_identifier,
  node_type,
  number_of_nodes,
  encrypted
from
  aws_redshift_cluster
where
  not encrypted;